#!/usr/bin/env python3
"""
Job application submit runner — action-based round-trip.

Reads a JSON action file, executes each action against a headed Playwright browser,
captures page state after all actions complete, and prints a JSON result to stdout.

Usage:
    python3 submit_runner.py <round.json>

The agent generates round.json, runs this script, reads the JSON output,
then generates the next round.json. Repeat until applied/blocked/error.

Browser state (cookies, localStorage) is persisted in `browser_state_dir`
so login sessions survive between rounds.

Exit codes:
    0 — round completed normally (check result.page.confirmed for submission)
    1 — blocked (CAPTCHA, login timeout)
    2 — fatal error
"""
import asyncio, json, os, shutil, socket, subprocess, sys, time
os.environ.setdefault("NODE_NO_WARNINGS", "1")
from pathlib import Path
from playwright.async_api import async_playwright, TimeoutError as PWTimeout

# Shared state dir — lives alongside tailored resumes
_SHARED_STATE = Path(os.environ.get("RESUME_OUTPUT_DIR", "/tmp")) / "state" / "_browser"
_CDP_PORT_FILE = _SHARED_STATE / "cdp_port.txt"
_USER_DATA_DIR = _SHARED_STATE / "user_data"   # persistent cookies / login state

# Progress log — tailed by orchestrator for real-time display
_PROGRESS_LOG = Path(os.environ.get("RESUME_OUTPUT_DIR", "/tmp")) / "state" / "submit_progress.log"
_TRACKER_PATH = os.environ.get("TRACKER_PATH", "")


def _log_progress(msg: str) -> None:
    """Append a timestamped line to the progress log (read by orchestrator in real-time)."""
    import datetime
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    try:
        _PROGRESS_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(_PROGRESS_LOG, "a") as f:
            f.write(f"{ts} 📨 {msg}\n")
    except OSError:
        pass


def _mark_applied(job_id: str) -> None:
    """Update the tracker row for job_id to 'applied'."""
    import re, datetime
    if not _TRACKER_PATH:
        return
    try:
        tracker = Path(_TRACKER_PATH)
        if not tracker.exists():
            return
        text = tracker.read_text()
        today = datetime.date.today().isoformat()
        # Match any row that contains the job_id slug in the Notes column
        # and has status resume_ready or blocked — replace with applied
        slug = job_id.replace("_", " ").lower()
        lines = text.splitlines()
        changed = False
        for i, line in enumerate(lines):
            if "| resume_ready |" not in line and "| blocked |" not in line:
                continue
            # Rough match: job_id slug words appear somewhere in the row
            words = [w for w in slug.split() if len(w) > 3]
            if not words or not any(w in line.lower() for w in words):
                continue
            lines[i] = re.sub(r'\|\s*(resume_ready|blocked)\s*\|',
                               f'| applied |', line, count=1)
            # Append applied date to Notes
            lines[i] = re.sub(r'(\|\s*applied\s*\|)([^|]*)\|',
                               lambda m: m.group(1) + m.group(2).rstrip()
                               + f' Applied {today}.|', lines[i], count=1)
            changed = True
            break
        if changed:
            tracker.write_text("\n".join(lines) + "\n")
    except Exception:
        pass


def _find_free_port() -> int:
    with socket.socket() as s:
        s.bind(("", 0))
        return s.getsockname()[1]


def _chromium_exe() -> str:
    # Prefer playwright's own chromium (most compatible with CDP)
    import glob
    for pattern in [
        str(Path.home() / ".cache/ms-playwright/chromium-*/chrome-linux64/chrome"),
        str(Path.home() / ".cache/ms-playwright/chromium-*/chrome-linux/chrome"),
    ]:
        hits = sorted(glob.glob(pattern), reverse=True)
        if hits:
            return hits[0]
    for candidate in [
        shutil.which("chromium-browser"),
        shutil.which("google-chrome"),
        shutil.which("chromium"),
    ]:
        if candidate and Path(candidate).exists():
            return candidate
    raise RuntimeError("Chromium not found")


async def _gc_tabs(browser, threshold=10, close_n=5):
    """If context has more than `threshold` tabs, close the `close_n` oldest.
    Protects about:blank placeholder and any tab matching a currently-held
    job hint URL (i.e. an active submit target)."""
    try:
        ctx = browser.contexts[0] if browser.contexts else None
        if ctx is None:
            return
        pages = list(ctx.pages)
        if len(pages) <= threshold:
            return
        # Collect active hint URLs from all job state dirs
        hints = set()
        try:
            state_root = _SHARED_STATE.parent  # .../state
            for f in state_root.glob("*/tab_url.txt"):
                hints.add(f.read_text().strip())
        except Exception:
            pass
        from urllib.parse import urlparse
        hint_hosts = {urlparse(h).netloc for h in hints if h}
        closed = 0
        for pg in pages:   # pages[0] is oldest
            if closed >= close_n:
                break
            try:
                if urlparse(pg.url).netloc in hint_hosts:
                    continue  # protect active job tabs
                await pg.close()
                closed += 1
            except Exception:
                pass
        if closed:
            _log(f"tab-gc: closed {closed} old tabs ({len(pages)}→{len(ctx.pages)})")
    except Exception as e:
        _log(f"tab-gc error: {e}")


async def _get_browser(p):
    """Connect to existing detached browser, or launch a new one."""
    _SHARED_STATE.mkdir(parents=True, exist_ok=True)
    _USER_DATA_DIR.mkdir(parents=True, exist_ok=True)

    if _CDP_PORT_FILE.exists():
        port = _CDP_PORT_FILE.read_text().strip()
        try:
            browser = await p.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
            _log(f"reconnected to browser on port {port}")
            await _gc_tabs(browser)
            return browser
        except Exception:
            _log(f"browser on port {port} gone — relaunching")
            _CDP_PORT_FILE.unlink(missing_ok=True)

    port = str(_find_free_port())
    exe  = _chromium_exe()
    # Launch chromium as a completely detached process — survives Python exit
    w = os.environ.get("BROWSER_WIDTH",  "800")
    h = os.environ.get("BROWSER_HEIGHT", "600")
    subprocess.Popen(
        [exe,
         f"--remote-debugging-port={port}",
         f"--user-data-dir={_USER_DATA_DIR}",
         "--no-first-run",
         "--no-default-browser-check",
         f"--window-size={w},{h}",
         "--window-position=50,50",
         "about:blank"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,   # detach from parent process group
    )
    _CDP_PORT_FILE.write_text(port)
    _log(f"launched browser on port {port}, waiting for CDP...")
    await asyncio.sleep(5)        # give Chromium time to start
    browser = await p.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
    _log("connected")
    return browser

# ── load actions file ─────────────────────────────────────────────────────────
if len(sys.argv) < 2:
    print(json.dumps({"error": "usage: submit_runner.py <round.json>"}))
    sys.exit(2)

with open(sys.argv[1]) as f:
    spec = json.load(f)

ROUND             = spec.get("round", 1)
JOB_ID            = spec.get("job_id", "unknown")
BROWSER_STATE_DIR = spec.get("browser_state_dir", f"/tmp/submit_state_{JOB_ID}")
ACTIONS           = spec.get("actions", [])

# Guard: detect if the same round number has been run too many times for this job.
# The agent sometimes rewrites round_1.json repeatedly — cap it to avoid infinite loops.
_MAX_SAME_ROUND = 4
_round_count_file = Path(BROWSER_STATE_DIR) / f".round_{ROUND}_count"
try:
    Path(BROWSER_STATE_DIR).mkdir(parents=True, exist_ok=True)
    _count = int(_round_count_file.read_text()) if _round_count_file.exists() else 0
    _count += 1
    _round_count_file.write_text(str(_count))
    if _count > _MAX_SAME_ROUND:
        _log_progress(f"✗ {JOB_ID} — round {ROUND} repeated {_count}x, marking blocked")
        print(json.dumps({
            "round": ROUND, "job_id": JOB_ID, "results": [],
            "page": {"url": "", "title": "", "interactive": [], "text": "",
                     "confirmed": False, "has_captcha": False, "has_login": False,
                     "is_generic_page": False, "is_not_found": False},
            "needs_login": [],
            "error": f"round {ROUND} repeated {_count} times — aborting to prevent infinite loop",
        }, ensure_ascii=False))
        sys.exit(1)
except Exception:
    pass

_log_progress(f"→ {JOB_ID}  round {ROUND}  ({len(ACTIONS)} actions)")

Path(BROWSER_STATE_DIR).mkdir(parents=True, exist_ok=True)


# ── helpers ───────────────────────────────────────────────────────────────────

def _log(msg):
    print(f"[runner] {msg}", file=sys.stderr, flush=True)


def _alert(msg: str = "") -> None:
    """Write alert to progress log (displayed by orchestrator) and play a sound."""
    if msg:
        _log_progress(f"⚠️  {msg}")
    # Terminal bell + system sound (best-effort — may not work in all contexts)
    print("\a", end="", flush=True)
    for cmd in [
        ["paplay", "/usr/share/sounds/freedesktop/stereo/bell.oga"],
        ["aplay",  "/usr/share/sounds/alsa/Front_Center.wav"],
        ["beep"],
    ]:
        try:
            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            break
        except FileNotFoundError:
            continue


def _ask(prompt: str, options: dict) -> str:
    """
    Ask the user via progress log. Since /dev/tty is unavailable in this context,
    we log the prompt and return the first option — the agent handles the response
    by reading page state after wait_human completes.
    """
    keys = "/".join(options.keys())
    choices = "  ".join(f"[{k}] {v}" for k, v in options.items())
    _log_progress(f"❓ {prompt}  ({choices})")
    return list(options.keys())[0]


async def capture_page_state(page) -> dict:
    """Return a compact snapshot the agent can use to plan the next round."""
    try:
        interactive = await page.evaluate("""() => {
            const out = [];
            document.querySelectorAll(
                'input:not([type=hidden]), select, textarea, button, [role="button"], label, a[href]'
            ).forEach(el => {
                const vis = el.offsetWidth > 0 || el.offsetHeight > 0 || el.getClientRects().length > 0;
                // Filter noise: skip invisible anchors that are clearly nav/footer.
                if (el.tagName === 'A' && !vis) {
                    const cls = (el.className || '').toString().toLowerCase();
                    if (/footer|menu__link|nav|header/.test(cls)) return;
                }
                out.push({
                    tag:         el.tagName,
                    type:        el.type || '',
                    name:        el.name || '',
                    id:          el.id || '',
                    placeholder: el.placeholder || '',
                    aria_label:  el.getAttribute('aria-label') || '',
                    value:       el.tagName === 'SELECT'
                                    ? (el.options[el.selectedIndex] || {}).text || ''
                                    : (el.value || '').slice(0, 80),
                    text:        el.textContent ? el.textContent.trim().slice(0, 60) : '',
                    required:    el.required || false,
                    visible:     vis,
                    disabled:    el.disabled || false,
                });
            });
            return out;
        }""")
    except Exception as e:
        interactive = [{"error": str(e)}]

    try:
        text_nodes = await page.evaluate("""() => {
            const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
            const out = [];
            let node;
            while ((node = walker.nextNode()) && out.length < 40) {
                const t = node.textContent.trim();
                if (t.length > 5 && t.length < 200) out.push(t);
            }
            return out;
        }""")
    except Exception:
        text_nodes = []

    body_text = " | ".join(text_nodes[:30])
    body_lower = body_text.lower()

    confirmed_phrases = [
        "application submitted", "application received", "successfully applied",
        "your application has been", "thank you for applying", "we received",
    ]
    captcha_phrases = ["captcha", "robot", "challenge", "cf-challenge", "verify you"]
    login_phrases   = ["sign in", "log in", "login", "create an account", "sign up",
                        "forgot password", "reset password", "register"]
    # Job no longer available
    not_found_phrases = [
        "job not found", "position has been filled", "no longer available",
        "this job has expired", "job has been removed", "posting expired",
        "this position is no longer", "page not found", "404 not found",
        "job posting is closed", "this role has been filled",
    ]
    # Words that, when present in the page <title>, mean the page is showing a
    # specific job posting (not a generic listing).
    role_keywords = [
        "engineer", "developer", "scientist", "analyst", "manager", "director",
        "lead", "architect", "researcher", "specialist", "consultant", "designer",
        "associate", "vice president", " vp", "head of", "principal",
        "quant", "trader", "strategist", "intern", "officer",
    ]
    # Title patterns that strongly indicate a generic listing / hub page.
    generic_title_patterns = [
        "jobs", "careers", "open positions", "openings", "job search",
        "search results", "all jobs", "find a job",
    ]

    url_lower   = page.url.lower()
    title       = await page.title()
    title_lower = title.lower()

    # URL looks generic if it ends at /careers or /jobs with no further segment
    import re as _re
    url_is_generic = bool(_re.search(r'/(careers|jobs|openings|opportunities)/?$', url_lower))

    title_has_role    = any(kw in title_lower for kw in role_keywords)
    title_is_generic  = (not title_has_role
                         and any(p in title_lower for p in generic_title_patterns))

    is_generic_page = url_is_generic or title_is_generic
    is_not_found = (any(p in body_lower for p in not_found_phrases)
                    or title_lower.startswith("error ")
                    or title_lower.endswith(" error")
                    or " | error" in title_lower)

    return {
        "url":            page.url,
        "title":          title,
        "interactive":    interactive,
        "text":           body_text[:1000],
        "confirmed":      any(p in body_lower for p in confirmed_phrases),
        "has_captcha":    any(p in body_lower for p in captcha_phrases),
        # URL-only login detection. Body-text phrases ("sign in", "create account")
        # are false positives on Workday/Oracle apply forms, which always render those
        # strings in headers even when the candidate is already logged in and filling
        # the form. Only flag login when the URL path itself is a login route.
        "has_login":      any(p in url_lower for p in ["/login", "/signin", "/sign-in", "/authgateway", "/account/login"]),
        "is_generic_page": is_generic_page,
        "is_not_found":   is_not_found,
    }


# ── action executors ──────────────────────────────────────────────────────────

async def exec_action(page, action: dict) -> dict:
    t    = action.get("type", "")
    res  = {"action": f"{t} {action.get('selector') or action.get('url') or ''}".strip()}

    try:
        if t == "navigate":
            await page.goto(action["url"], wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_load_state("networkidle", timeout=10000)
            res["status"] = "ok"

        elif t == "wait":
            await asyncio.sleep(action.get("ms", 1000) / 1000)
            res["status"] = "ok"

        elif t == "wait_nav":
            await page.wait_for_load_state("networkidle", timeout=15000)
            res["status"] = "ok"

        elif t == "fill":
            sel = action["selector"]
            el  = page.locator(sel).first
            if await el.count() > 0:
                await el.scroll_into_view_if_needed()
                await el.fill(action.get("value", ""))
                res["status"] = "ok"
            else:
                res["status"] = "not_found"

        elif t == "select":
            sel = action["selector"]
            el  = page.locator(sel).first
            if await el.count() == 0:
                res["status"] = "not_found"
            else:
                want_label = action.get("label", None)
                want_value = action.get("value", "")
                # First try Playwright's native select_option
                try:
                    await el.select_option(value=want_value, label=want_label)
                except Exception as e:
                    # Will retry via JS fallback below
                    res["error"] = f"select_option threw: {e}"
                # Verify it actually took effect — Select2 wrappers, hidden
                # selects, and aria-hidden elements often cause select_option
                # to succeed silently without changing selectedIndex.
                _verify_js = """(el, want) => {
  if (el.tagName !== 'SELECT') return {ok:false,reason:'not a select'};
  if (el.selectedIndex > 0) {
    const opt = el.options[el.selectedIndex];
    if (want.label && opt.text !== want.label) return {ok:false,reason:'wrong label',got:opt.text};
    if (want.value && opt.value !== String(want.value)) return {ok:false,reason:'wrong value',got:opt.value};
    return {ok:true,value:opt.value,text:opt.text};
  }
  let opt = null;
  if (want.label) opt = Array.from(el.options).find(o => o.text === want.label);
  if (!opt && want.value) opt = Array.from(el.options).find(o => o.value === String(want.value));
  if (!opt) return {ok:false,reason:'option not in DOM'};
  el.value = opt.value;
  el.dispatchEvent(new Event('change',{bubbles:true}));
  if (window.jQuery && window.jQuery(el).data('select2')) window.jQuery(el).trigger('change');
  return el.selectedIndex > 0 ? {ok:true,value:opt.value,text:opt.text,via:'js'} : {ok:false,reason:'js set failed'};
}"""
                try:
                    state = await el.evaluate(_verify_js, {"label": want_label, "value": want_value})
                except Exception as e:
                    state = {"ok": False, "reason": f"verify threw: {e}"}
                if state.get("ok"):
                    res["status"] = "ok"
                    res["selected"] = {"text": state.get("text"), "value": state.get("value")}
                    if state.get("via"): res["via"] = state["via"]
                    res.pop("error", None)
                else:
                    res["status"] = "error"
                    res["error"] = f"select did not take effect: {state.get('reason')}; got={state.get('got','')}"

        elif t == "click":
            sel    = action["selector"]
            iframe = action.get("iframe")  # optional CSS selector for an iframe
            if iframe:
                # Click an element inside a (possibly cross-origin) iframe.
                el = page.frame_locator(iframe).locator(sel).first
            else:
                el = page.locator(sel).first
            if await el.count() > 0:
                try:
                    await el.scroll_into_view_if_needed()
                except Exception:
                    pass  # frame_locator elements may not support this
                await el.click()
                res["status"] = "ok"
            else:
                res["status"] = "not_found"

        elif t == "upload":
            # Two modes:
            #   1. Direct: set files on the <input type=file> via `selector`.
            #   2. Via trigger: click `click_selector` inside expect_file_chooser,
            #      then provide files through the chooser event. Use this when the
            #      real input is hidden behind a "Choose File" button that opens
            #      the OS picker on click.
            paths = action.get("paths") or [action.get("path")]
            valid_paths = [p for p in paths if p and Path(p).exists()]
            click_sel = action.get("click_selector")
            if click_sel:
                trigger = page.locator(click_sel).first
                if await trigger.count() == 0:
                    res["status"] = "not_found"
                else:
                    try:
                        async with page.expect_file_chooser(timeout=10000) as fc_info:
                            await trigger.click()
                        chooser = await fc_info.value
                        await chooser.set_files(valid_paths)
                        res["status"] = "ok"
                    except PWTimeout:
                        res["status"] = "timeout"
                        res["error"]  = "click did not open a file chooser"
            else:
                sel = action["selector"]
                iframe_sel = action.get("iframe")
                if iframe_sel:
                    el = page.frame_locator(iframe_sel).locator(sel).first
                else:
                    el  = page.locator(sel).first
                if await el.count() > 0:
                    await el.set_input_files(valid_paths)
                    res["status"] = "ok"
                else:
                    res["status"] = "not_found"

        elif t == "type":
            sel = action["selector"]
            el  = page.locator(sel).first
            if await el.count() > 0:
                await el.type(action.get("value", ""), delay=50)
                res["status"] = "ok"
            else:
                res["status"] = "not_found"

        elif t == "press":
            await page.keyboard.press(action.get("key", "Tab"))
            res["status"] = "ok"

        elif t == "evaluate":
            result = await page.evaluate(action["expression"])
            res["status"] = "ok"
            res["result"] = result

        elif t == "check_login":
            # Detection-only. Never blocks. Returns status=needs_login if not
            # signed in — the agent decides what to do next (SSO click,
            # wait_human_login, Forgot Password, etc.) via its decision tree.
            sel        = action.get("logged_in_selector", "")
            site       = action.get("site", page.url)
            login_url  = action.get("login_url", "")
            logged_in  = False
            if sel:
                try:
                    logged_in = await page.locator(sel).count() > 0
                except Exception:
                    pass
            res["site"] = site
            if logged_in:
                res["status"] = "already_logged_in"
            else:
                res["status"]    = "needs_login"
                res["login_url"] = login_url

        elif t == "fetch_email_code":
            # Open a new tab, go to webmail, search for recent verification email,
            # extract the code, close the tab, return the code in result.
            email    = action.get("email", os.environ.get("USER_EMAIL", ""))
            provider = action.get("provider", "")   # "gmail" | "outlook" | auto-detect
            timeout  = action.get("timeout_s", 120) # wait up to N seconds for email to arrive
            # Gmail search query to isolate the target email. Strongly recommended —
            # without it the scanner sees the entire Gmail UI and picks up false positives.
            # Examples: "from:bloomberg", "subject:reset", "from:noreply@workday.com newer_than:10m"
            search_query = action.get("search_query", "newer_than:10m")

            # Auto-detect provider from email domain
            if not provider:
                domain = email.split("@")[-1].lower() if "@" in email else ""
                if "gmail" in domain:
                    provider = "gmail"
                elif domain in ("outlook.com", "hotmail.com", "live.com", "msn.com"):
                    provider = "outlook"
                else:
                    provider = "gmail"  # fallback

            # Per-provider config: inbox URL, sign-in host (means NOT signed in),
            # and the provider's own domains to exclude when scanning for reset links.
            from urllib.parse import quote as _q
            WEBMAIL = {
                "gmail": {
                    "url":         f"https://mail.google.com/mail/u/0/#search/{_q(search_query)}",
                    "signin_host": "accounts.google.com",
                    "own_domains": ("accounts.google.com", "mail.google.com"),
                },
                "outlook": {
                    "url":         "https://outlook.live.com/mail/0/",
                    "signin_host": "login.live.com",
                    "own_domains": ("login.live.com", "outlook.live.com", "outlook.office.com"),
                },
            }
            cfg = WEBMAIL.get(provider, WEBMAIL["gmail"])
            url = cfg["url"]

            _log(f"Opening {provider} to fetch verification code or reset link...")
            original_page = page
            ctx0 = page.context
            email_page = await ctx0.new_page()
            await email_page.goto(url, wait_until="domcontentloaded")
            await asyncio.sleep(4)

            # Detect if webmail is signed-in. If we're on accounts.google.com / login.live.com,
            # the inbox isn't loaded — bail out instead of regex-matching the sign-in page.
            cur_url = email_page.url.lower()
            if cfg["signin_host"] in cur_url:
                _log(f"  webmail not signed in (at {cur_url[:80]})")
                await email_page.close()
                try: await original_page.bring_to_front()
                except Exception: pass
                res["status"] = "webmail_not_signed_in"
                res["error"]  = f"{provider} requires sign-in; please log in to webmail manually"
                return res

            WEBMAIL_DOMAINS = cfg["own_domains"]

            # Open the first email in the search result so we scan its body,
            # not the entire Gmail UI (which has huge amounts of noise).
            async def _open_first_email():
                if provider != "gmail":
                    return False
                try:
                    first_row = email_page.locator("tr.zA").first
                    if await first_row.count() > 0:
                        await first_row.click()
                        await asyncio.sleep(1.5)
                        return True
                except Exception:
                    pass
                return False

            code = None
            link = None
            import re as _re
            deadline = time.time() + timeout
            opened_email = False
            while time.time() < deadline and not code and not link:
                if not opened_email:
                    opened_email = await _open_first_email()
                try:
                    # Use visible inner_text to skip CSS/JS/hex color noise.
                    # Keep raw HTML as fallback for href extraction.
                    try:
                        visible = await email_page.locator("body").inner_text(timeout=3000)
                    except Exception:
                        visible = ""
                    raw_html = await email_page.content()
                    # Scan links on raw HTML (so href attributes are seen),
                    # scan codes on visible text only.
                    content = raw_html
                    content_lower = content.lower()
                    # Look for password reset / verification links (common patterns)
                    link_patterns = [
                        r'https?://[^\s"\'<>]+[/?&=](?:reset|verify|confirm|activate|password)[a-z_-]*[/?&=][^\s"\'<>]{10,}',
                        r'https?://[^\s"\'<>]+[?&]token=[^\s"\'<>]{10,}',
                        r'https?://[^\s"\'<>]+[?&]code=[^\s"\'<>]{6,}',
                    ]
                    # Static/CDN hosts that never contain real reset links.
                    STATIC_HOSTS = ('gstatic.com', 'googleusercontent.com', 'googleapis.com',
                                    'fonts.gstatic.com', 'www.w3.org', 'schema.org')
                    for pat in link_patterns:
                        hits = _re.findall(pat, content, _re.IGNORECASE)
                        hits = [h for h in hits if not any(x in h.lower() for x in
                                ['unsubscribe', 'pixel', 'tracking', 'open.php', 'click.php',
                                 '.png', '.jpg', '.gif', '.css', '.js', '.svg'])
                                and not any(d in h.lower() for d in WEBMAIL_DOMAINS)
                                and not any(d in h.lower() for d in STATIC_HOSTS)]
                        if hits:
                            link = hits[0]
                            _log(f"  found reset link: {link[:80]}...")
                            break
                    if not link:
                        # Fall back to numeric OTP codes — scan visible text only
                        matches = _re.findall(r'\b(\d{4,8})\b', visible)
                        if matches:
                            six_digit = [m for m in matches if len(m) == 6]
                            code = six_digit[0] if six_digit else matches[0]
                            _log(f"  found code: {code}")
                except Exception:
                    pass
                if not code and not link:
                    await asyncio.sleep(5)
                    # Go back to the search results and retry opening the first email
                    await email_page.goto(url, wait_until="domcontentloaded")
                    await asyncio.sleep(2)
                    opened_email = False

            await email_page.close()
            # Bring original page back to front
            try:
                await original_page.bring_to_front()
            except Exception:
                pass

            if link:
                res["status"] = "ok"
                res["link"]   = link
                res["code"]   = ""   # agent checks result.link first
                _log_progress(f"📧 {JOB_ID} — got reset link from email")
            elif code:
                res["status"] = "ok"
                res["code"]   = code
                _log_progress(f"📧 {JOB_ID} — got code {code} from email")
            else:
                _alert(f"Could not find verification code or reset link in {provider} after {timeout}s")
                _log_progress(f"✗ {JOB_ID} — no code/link found in email after {timeout}s")
                res["status"] = "code_not_found"

        elif t == "wait_human_login":
            # Ask user to log in manually; if no login detected within timeout,
            # returns status="timeout" so the agent can proceed with Forgot Password.
            reason  = action.get("reason", "Login required")
            timeout = action.get("timeout_s", int(os.environ.get("LOGIN_HUMAN_TIMEOUT", "60")))
            _alert(f"{reason} — {page.url}")
            _log_progress(
                f"⏳ {JOB_ID} — {reason}. "
                f"Log in manually in the browser within {timeout}s, "
                f"or it will auto-try Forgot Password."
            )
            deadline = time.time() + timeout
            logged_in = False
            while time.time() < deadline:
                await asyncio.sleep(5)
                try:
                    content = (await page.evaluate("document.body.innerText")).lower()
                    still_login = any(p in content for p in
                                      ["sign in", "log in", "login", "forgot password"])
                    if not still_login:
                        logged_in = True
                        _log_progress(f"✓ {JOB_ID} — manual login detected")
                        break
                except Exception:
                    pass
                remaining = int(deadline - time.time())
                if remaining > 0 and remaining % 20 == 0:
                    _log_progress(f"⏳ {JOB_ID} — {reason} ({remaining}s left, then auto Forgot Password)")
            if logged_in:
                res["status"] = "ok"
            else:
                res["status"]       = "timeout"
                res["auto_proceed"] = True
                _log_progress(f"⚠ {JOB_ID} — no manual login in {timeout}s, proceeding with Forgot Password")

        elif t == "wait_human":
            reason  = action.get("reason", "human needed")
            timeout = action.get("timeout_s", 120)
            _alert(f"{reason} — {page.url}")
            _log_progress(f"⚠️  {JOB_ID} — waiting for human: {reason}")
            deadline = time.time() + timeout
            while time.time() < deadline:
                await asyncio.sleep(5)
                remaining = int(deadline - time.time())
                if remaining % 20 == 0:
                    _log(f"  waiting for human... {remaining}s left")
                    _log_progress(f"⏳ {JOB_ID} — {reason} ({remaining}s left)")
            res["status"] = "timeout"

        else:
            res["status"] = "unknown_action"
            res["error"]  = f"unknown action type: {t!r}"

    except PWTimeout as e:
        res["status"] = "timeout"
        res["error"]  = str(e)[:120]
    except Exception as e:
        res["status"] = "error"
        res["error"]  = str(e)[:200]

    return res


# ── main ──────────────────────────────────────────────────────────────────────

async def main():
    _log(f"round {ROUND} — {JOB_ID} — {len(ACTIONS)} actions")

    async with async_playwright() as p:
        browser = await _get_browser(p)

        # Round 1 always opens a fresh tab so the previous job's page stays visible.
        # Subsequent rounds reuse the current tab (last open page for this job).
        ctx = browser.contexts[0] if browser.contexts else await browser.new_context()
        tab_hint_file = Path(BROWSER_STATE_DIR) / "tab_url.txt"
        if ROUND == 1:
            page = await ctx.new_page()
        else:
            # Find the tab we were working on. Require a recorded hint — if it's
            # missing or no matching tab exists, fail loudly rather than silently
            # picking a random page (which has caused job cross-contamination).
            if not tab_hint_file.exists():
                print(json.dumps({"round": ROUND, "job_id": JOB_ID,
                    "results": [{"action": "tab_lookup", "status": "error",
                                 "error": "no tab hint recorded — run round 1 first"}]}))
                sys.exit(2)
            hint = tab_hint_file.read_text().strip()
            from urllib.parse import urlparse
            h = urlparse(hint)
            page = None
            for pg in ctx.pages:
                u = urlparse(pg.url)
                if u.netloc == h.netloc:
                    page = pg
                    break
            if page is None:
                urls = [pg.url for pg in ctx.pages]
                print(json.dumps({"round": ROUND, "job_id": JOB_ID,
                    "results": [{"action": "tab_lookup", "status": "error",
                                 "error": f"expected tab on host {h.netloc} (hint={hint[:80]}) "
                                          f"not found among open tabs",
                                 "open_tabs": urls}]}))
                sys.exit(2)
            _log(f"  resumed tab: {page.url[:80]}")
            try: await page.bring_to_front()
            except Exception: pass

        results = []
        for action in ACTIONS:
            # Special: close_tab closes current page (but only if not last)
            if action.get("type") == "close_tab":
                all_pages = [pg for ctx in browser.contexts for pg in ctx.pages]
                if len(all_pages) > 1:
                    await page.close()
                    _log("  closed tab")
                else:
                    _log("  last tab — keeping open")
                results.append({"action": "close_tab", "status": "ok"})
                continue

            pages_before = len(ctx.pages)
            r = await exec_action(page, action)
            results.append(r)
            _log(f"  {r['status']:12} {r['action']}")
            # If the action opened a new tab (popup), switch to it.
            if len(ctx.pages) > pages_before:
                page = ctx.pages[-1]
                try:
                    await page.wait_for_load_state("domcontentloaded", timeout=8000)
                except Exception:
                    pass
                await page.bring_to_front()
                _log(f"  switched to new tab: {page.url[:80]}")
            if r["status"] in ("timeout", "error") and action.get("abort_on_error"):
                break

        # Wait for page to settle before snapshot
        try:
            await page.wait_for_load_state("networkidle", timeout=5000)
        except Exception:
            pass

        page_state = await capture_page_state(page)

        # Persist the current tab's URL so subsequent rounds can re-find it
        # even if the user (or other scripts) opened additional tabs after it.
        try:
            tab_hint_file.write_text(page.url)
        except Exception:
            pass

        # On confirmed submission: update tracker + close tab
        if page_state.get("confirmed"):
            _mark_applied(JOB_ID)
            try:
                all_pages = [pg for ctx in browser.contexts for pg in ctx.pages]
                if len(all_pages) > 1:
                    await page.close()
            except Exception:
                pass

        # Log round result for real-time visibility
        if page_state.get("confirmed"):
            _log_progress(f"✓ {JOB_ID} — submitted!")
        elif page_state.get("has_login"):
            _log_progress(f"⚠ {JOB_ID} — round {ROUND} ended on login page")
        elif page_state.get("has_captcha"):
            _log_progress(f"⚠ {JOB_ID} — round {ROUND} ended on captcha")
        elif any(r.get("status") == "error" for r in results):
            errors = [r.get("error","?") for r in results if r.get("status") == "error"]
            _log_progress(f"✗ {JOB_ID} — round {ROUND} error: {errors[0][:80]}")

        # Disconnect from CDP without killing the browser process
        # (browser stays open for next round / next job)

    needs_login = [r["site"] for r in results
                   if r.get("status") == "needs_login" and r.get("site")]
    output = {
        "round":       ROUND,
        "job_id":      JOB_ID,
        "results":     results,
        "page":        page_state,
        "needs_login": needs_login,
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
