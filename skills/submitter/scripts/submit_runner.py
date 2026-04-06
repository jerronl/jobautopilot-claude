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
from pathlib import Path
from playwright.async_api import async_playwright, TimeoutError as PWTimeout

# Shared state dir — lives alongside tailored resumes
_SHARED_STATE = Path(os.environ.get("RESUME_OUTPUT_DIR", "/tmp")) / "state" / "_browser"
_CDP_PORT_FILE = _SHARED_STATE / "cdp_port.txt"
_USER_DATA_DIR = _SHARED_STATE / "user_data"   # persistent cookies / login state

# Progress log — tailed by orchestrator for real-time display
_PROGRESS_LOG = Path(os.environ.get("RESUME_OUTPUT_DIR", "/tmp")) / "state" / "submit_progress.log"


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


def _find_free_port() -> int:
    with socket.socket() as s:
        s.bind(("", 0))
        return s.getsockname()[1]


def _chromium_exe() -> str:
    for candidate in [
        shutil.which("chromium-browser"),
        shutil.which("chromium"),
        shutil.which("google-chrome"),
        # playwright's own chromium
        str(Path.home() / ".cache/ms-playwright/chromium-*/chrome-linux/chrome"),
    ]:
        if candidate and Path(candidate).exists():
            return candidate
    # fallback: let playwright find it
    import glob
    hits = glob.glob(str(Path.home() / ".cache/ms-playwright/chromium-*/chrome-linux/chrome"))
    if hits:
        return hits[0]
    raise RuntimeError("Chromium not found")


async def _get_browser(p):
    """Connect to existing detached browser, or launch a new one."""
    _SHARED_STATE.mkdir(parents=True, exist_ok=True)
    _USER_DATA_DIR.mkdir(parents=True, exist_ok=True)

    if _CDP_PORT_FILE.exists():
        port = _CDP_PORT_FILE.read_text().strip()
        try:
            browser = await p.chromium.connect_over_cdp(f"http://localhost:{port}")
            _log(f"reconnected to browser on port {port}")
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
    await asyncio.sleep(2)        # give Chromium time to start
    browser = await p.chromium.connect_over_cdp(f"http://localhost:{port}")
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
                'input:not([type=hidden]), select, textarea, button, [role="button"], label'
            ).forEach(el => {
                const vis = el.offsetWidth > 0 || el.offsetHeight > 0 || el.getClientRects().length > 0;
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

    return {
        "url":         page.url,
        "title":       await page.title(),
        "interactive": interactive,
        "text":        body_text[:1000],
        "confirmed":   any(p in body_lower for p in confirmed_phrases),
        "has_captcha": any(p in body_lower for p in captcha_phrases),
        "has_login":   (any(p in body_lower for p in login_phrases)
                        or any(p in page.url.lower() for p in ["/login", "/signin", "/sign-in", "/auth", "authgateway"])),
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
            if await el.count() > 0:
                await el.select_option(value=action.get("value", ""),
                                       label=action.get("label", None))
                res["status"] = "ok"
            else:
                res["status"] = "not_found"

        elif t == "click":
            sel = action["selector"]
            el  = page.locator(sel).first
            if await el.count() > 0:
                await el.scroll_into_view_if_needed()
                await el.click()
                res["status"] = "ok"
            else:
                res["status"] = "not_found"

        elif t == "upload":
            sel   = action["selector"]
            paths = action.get("paths") or [action.get("path")]
            el    = page.locator(sel).first
            if await el.count() > 0:
                await el.set_input_files([p for p in paths if p and Path(p).exists()])
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
            sel       = action.get("logged_in_selector", "")
            site      = action.get("site", page.url)
            login_url = action.get("login_url", "")
            signup_url = action.get("signup_url", "")
            logged_in = False
            if sel:
                try:
                    logged_in = await page.locator(sel).count() > 0
                except Exception:
                    pass
            if logged_in:
                res["status"] = "already_logged_in"
                res["site"]   = site
            else:
                _alert(f"Login needed for {site}")
                choice = _ask(
                    f"Need to log in to {site}.",
                    {
                        "l": "I have an account — open login page",
                        "c": "I need to create an account — open signup page",
                        "s": "Skip this site for now",
                    },
                )
                res["site"]   = site
                if choice == "s":
                    res["status"] = "skipped"
                else:
                    dest = login_url if choice == "l" else (signup_url or login_url)
                    if dest:
                        await page.goto(dest, wait_until="domcontentloaded")
                    _log(f"Waiting for you to complete login/signup (up to 5 min)...")
                    deadline = time.time() + 300
                    while time.time() < deadline:
                        await asyncio.sleep(5)
                        try:
                            if sel and await page.locator(sel).count() > 0:
                                _log(f"  ✓ logged in to {site}")
                                res["status"] = "logged_in"
                                break
                        except Exception:
                            pass
                        remaining = int(deadline - time.time())
                        if remaining % 30 == 0:
                            _log(f"  still waiting... {remaining}s left")
                    else:
                        res["status"] = "login_timeout"

        elif t == "fetch_email_code":
            # Open a new tab, go to webmail, search for recent verification email,
            # extract the code, close the tab, return the code in result.
            email    = action.get("email", os.environ.get("USER_EMAIL", ""))
            provider = action.get("provider", "")   # "gmail" | "outlook" | auto-detect
            timeout  = action.get("timeout_s", 120) # wait up to N seconds for email to arrive

            # Auto-detect provider from email domain
            if not provider:
                domain = email.split("@")[-1].lower() if "@" in email else ""
                if "gmail" in domain:
                    provider = "gmail"
                elif domain in ("outlook.com", "hotmail.com", "live.com", "msn.com"):
                    provider = "outlook"
                else:
                    provider = "gmail"  # fallback

            WEBMAIL = {
                "gmail":   "https://mail.google.com/mail/u/0/#search/newer_than%3A10m",
                "outlook": "https://outlook.live.com/mail/0/",
            }
            url = WEBMAIL.get(provider, WEBMAIL["gmail"])

            _log(f"Opening {provider} to fetch verification code or reset link...")
            original_page = page
            ctx0 = browser.contexts[0] if browser.contexts else None
            email_page = await ctx0.new_page() if ctx0 else await page.context.new_page()
            await email_page.goto(url, wait_until="domcontentloaded")
            await asyncio.sleep(4)

            code = None
            link = None
            import re as _re
            deadline = time.time() + timeout
            while time.time() < deadline and not code and not link:
                try:
                    content = await email_page.content()
                    content_lower = content.lower()
                    # Look for password reset / verification links (common patterns)
                    link_patterns = [
                        r'https?://[^\s"\'<>]+(?:reset|verify|confirm|activate|password)[^\s"\'<>]{10,}',
                        r'https?://[^\s"\'<>]+token=[^\s"\'<>]{10,}',
                        r'https?://[^\s"\'<>]+code=[^\s"\'<>]{6,}',
                    ]
                    for pat in link_patterns:
                        hits = _re.findall(pat, content, _re.IGNORECASE)
                        # Filter out tracking pixels, unsubscribe links, etc.
                        hits = [h for h in hits if not any(x in h.lower() for x in
                                ['unsubscribe', 'pixel', 'tracking', 'open.php', 'click.php'])]
                        if hits:
                            link = hits[0]
                            _log(f"  found reset link: {link[:80]}...")
                            break
                    if not link:
                        # Fall back to numeric OTP codes
                        matches = _re.findall(r'\b(\d{4,8})\b', content)
                        if matches:
                            six_digit = [m for m in matches if len(m) == 6]
                            code = six_digit[0] if six_digit else matches[0]
                            _log(f"  found code: {code}")
                except Exception:
                    pass
                if not code and not link:
                    await asyncio.sleep(5)
                    await email_page.reload(wait_until="domcontentloaded")

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

        # Reuse existing page or open a new tab
        pages = browser.contexts[0].pages if browser.contexts else []
        page  = pages[-1] if pages else await browser.contexts[0].new_page() if browser.contexts else await (await browser.new_context()).new_page()

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

            r = await exec_action(page, action)
            results.append(r)
            _log(f"  {r['status']:12} {r['action']}")
            if r["status"] in ("timeout", "error") and action.get("abort_on_error"):
                break

        # Wait for page to settle before snapshot
        try:
            await page.wait_for_load_state("networkidle", timeout=5000)
        except Exception:
            pass

        page_state = await capture_page_state(page)

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
