"""Orchestrator — coordinates search → tailor → submit pipeline."""
import os
import re
import anyio
from pathlib import Path
from claude_agent_sdk import (
    query, ClaudeAgentOptions, ResultMessage, AssistantMessage, TextBlock,
    ThinkingBlock, ToolUseBlock, TaskStartedMessage, TaskProgressMessage,
)

_CYAN    = "\033[36m"
_GREEN   = "\033[32m"
_RED     = "\033[31m"
_MAGENTA = "\033[35m"
_DIM     = "\033[2m"
_RESET   = "\033[0m"

_ANSI_RE = re.compile(r'\033\[[0-9;]*m')  # strip existing ANSI codes before recoloring

_ICONS = {
    "[Orchestrator]": "🎬",
    "[Tailor]":       "✂️ ",
    "[Search]":       "🔍",
    "[Submitter]":    "📨",
}

_ERASE_LINE = "\r\033[2K"   # go to line start, erase entire line

_line_buf           = ""
_last_tool          = ""
_tool_count         = 0
_last_tool_ts       = 0.0
_progress_on_screen = False   # True while an inline progress line is showing
_submit_log_pos     = 0       # byte offset into submit_progress.log already displayed
_search_log_pos     = 0       # byte offset into search_progress.log already displayed


def _clear_progress() -> None:
    global _last_tool, _tool_count, _last_tool_ts
    _last_tool = ""
    _tool_count = 0
    _last_tool_ts = 0.0


def _poll_submit_log() -> None:
    """Print any new lines written to submit_progress.log since last poll."""
    global _submit_log_pos
    resume_output_dir = os.environ.get("RESUME_OUTPUT_DIR", str(Path.home() / "Documents" / "jobs" / "tailored")).rstrip("/")
    log_path = Path(resume_output_dir) / "state" / "submit_progress.log"
    try:
        if not log_path.exists():
            return
        with open(log_path, "r") as f:
            f.seek(_submit_log_pos)
            new = f.read()
            _submit_log_pos = f.tell()
        for line in new.splitlines():
            if line.strip():
                _flush_line(line)
    except OSError:
        pass


def _poll_search_log() -> None:
    """Print any new lines written to search_progress.log since last poll."""
    global _search_log_pos
    log_path = WORKSPACE / "state" / "search_progress.log"
    try:
        if not log_path.exists():
            return
        with open(log_path, "r") as f:
            f.seek(_search_log_pos)
            new = f.read()
            _search_log_pos = f.tell()
        for line in new.splitlines():
            if line.strip():
                _flush_line(line)
    except OSError:
        pass


def _show_progress(tool: str) -> None:
    import datetime, time
    global _last_tool, _tool_count, _last_tool_ts, _progress_on_screen
    now = time.time()
    _tool_count += 1
    if tool == _last_tool and _tool_count < 10 and (now - _last_tool_ts) < 5:
        return
    _last_tool    = tool
    _last_tool_ts = now
    ts = datetime.datetime.now().strftime('%H:%M:%S')
    count_str = f" ×{_tool_count}" if _tool_count > 1 else ""
    # Print inline (no newline) so real content can overwrite it
    print(f"{_ERASE_LINE}{_DIM}{ts} [{tool}{count_str}]{_RESET}", end="", flush=True)
    _progress_on_screen = True
    _tool_count = 0


def _flush_line(line: str) -> None:
    import datetime
    global _progress_on_screen
    _clear_progress()
    # If a progress line is showing inline, erase it before printing real content
    prefix = _ERASE_LINE if _progress_on_screen else ""
    _progress_on_screen = False
    clean = _ANSI_RE.sub('', line)
    if not clean.strip():
        print(prefix)
        return
    for tag, icon in _ICONS.items():
        clean = clean.replace(tag, icon)
    ts = f"{_DIM}{datetime.datetime.now().strftime('%H:%M:%S')}{_RESET} "
    if re.search(r'\*\*Progress:', clean):
        print(f"{prefix}{ts}{_MAGENTA}{clean}{_RESET}")
        return
    if re.match(r'\[task:', clean):
        print(f"{prefix}{ts}{_DIM}{clean}{_RESET}")
        return
    colored = clean.replace('✓', f'{_GREEN}✓{_RESET}')
    colored = colored.replace('✗', f'{_RED}✗{_RESET}')
    print(f"{prefix}{ts}{colored}")

def _stream_text(text: str) -> None:
    global _line_buf
    _line_buf += text
    while "\n" in _line_buf:
        line, _line_buf = _line_buf.split("\n", 1)
        _flush_line(line)

from .base import base_env, WORKSPACE, SKILLS_DIR, REPO_ROOT
from .search import definition as search_def
from .tailor import definition as tailor_def
from .submitter import definition as submitter_def

_DEFAULT_LOGIN_TIMEOUT = 60   # seconds


def _tracker_get_setting(key: str) -> str | None:
    """Read a value from the ## Settings table in the tracker."""
    tracker = WORKSPACE / "job_application_tracker.md"
    if not tracker.exists():
        return None
    import re
    text = tracker.read_text()
    m = re.search(rf'^\|\s*{re.escape(key)}\s*\|\s*([^|]+?)\s*\|', text, re.MULTILINE)
    return m.group(1).strip() if m else None


def _tracker_set_setting(key: str, value: str) -> None:
    """Write/update a value in the ## Settings table in the tracker, creating the section if needed."""
    import re
    tracker = WORKSPACE / "job_application_tracker.md"
    if not tracker.exists():
        return
    text = tracker.read_text()
    row = f"| {key} | {value} |"
    # Update existing row
    pattern = rf'^\|\s*{re.escape(key)}\s*\|[^|]*\|'
    if re.search(pattern, text, re.MULTILINE):
        text = re.sub(pattern, row, text, flags=re.MULTILINE)
    elif "## Settings" in text:
        # Append row to existing Settings table
        text = re.sub(
            r'(## Settings.*?\|[-| ]+\|)(.*?)(\n## |\Z)',
            lambda m: m.group(1) + m.group(2) + f"\n{row}" + m.group(3),
            text, flags=re.DOTALL
        )
    else:
        # Add Settings section before ## Jobs
        settings_block = (
            "\n## Settings\n\n"
            "| Key | Value |\n"
            "|-----|-------|\n"
            f"{row}\n"
        )
        text = re.sub(r'(\n## Jobs)', settings_block + r'\1', text)
    tracker.write_text(text)



SYSTEM_PROMPT = f"""\
You are the Job Autopilot orchestrator. You coordinate a three-stage pipeline
by delegating to specialized subagents using the Agent tool.

## Pipeline stages

1. **job-search** — Search job boards, filter results, write to tracker.
   Invoke when: user wants to find new jobs.
   After the search agent returns, relay its output line by line using `[Search]` prefix:
     [Search] ✓ Goldman Sachs — Quant Developer  (shortlisted; ...)
     [Search] ✗ JPMorgan — Junior Analyst  (screen_reject: too junior)
   Then print a one-line summary: jobs found, shortlisted, rejected.

2. **resume-tailor** — Writes tailored .md files (resume + cover letter) for each shortlisted job.
   The tailor agent produces ONLY .md files. After each tailor call returns, YOU must:

   a) Convert resume .md → .docx:
      python3 $MD_TO_DOCX_SCRIPT "<resume.md>" "$RESUME_TEMPLATE" "<resume.docx>"
      Then update the tracker: set resume_path = "<resume.docx>" (replace .md extension with .docx)

   b) Verify tables > 0:
      python3 -c "from docx import Document; d=Document('<resume.docx>'); assert len(d.tables)>0, 'BAD FORMAT'"

   b2) Convert cover letter .md → .docx (plain text, no template):
      python3 - << 'PYEOF'
      import sys
      from pathlib import Path
      from docx import Document
      from docx.shared import Pt, Inches
      md = Path("<cover_letter.md>").read_text()
      doc = Document()
      for sec in doc.sections:
          sec.top_margin = Inches(1); sec.bottom_margin = Inches(1)
          sec.left_margin = Inches(1); sec.right_margin = Inches(1)
      style = doc.styles['Normal']
      style.font.name = 'Calibri'; style.font.size = Pt(11)
      for line in md.strip().split('\n'):
          doc.add_paragraph(line)
      doc.save("<cover_letter.docx>")
      PYEOF
      Then update the tracker: set cover_letter_path = "<cover_letter.docx>" (replace .md extension with .docx)

   c) Check resume .md content against the source resume in $RESUME_DIR:
      - Line 1 name must exactly match the name in the source resume
      - All companies and roles listed must exist in the source resume (no invented employers)
      - EARLIER EXPERIENCE section must include all employers beyond the top 5 jobs
      - EARLIER EXPERIENCE entries must be ONE LINE EACH — no bullets, no second line (grep -A1 "EARLIER EXPERIENCE" to check)
      - Bullet point facts (tools, metrics, product names) must be traceable to the source resume
      - No invented details in any bullet

   d) If any check fails: ask tailor to fix the .md, then re-convert.

   e) Print one result line per job (see output format below).

   Invoke tailor in batches of up to 10 jobs. After each batch returns, run steps a–e for
   every job in the batch, then launch the next batch. While waiting for tailor, submitter
   and search can be running in parallel.

3. **job-submitter** — Submits applications via iterative code-act loop (write actions JSON →
   run submit_runner.py → read page state → repeat). Handles its own execution loop internally.
   Invoke when: tracker has `resume_ready` or `blocked` entries.
   After it returns, relay its output line by line using `[Submitter]` prefix.

## Shortlist target

`JOB_SEARCH_SHORTLIST_TARGET` is the max number of active jobs in the pipeline at once.
Before invoking job-search, count rows with status `shortlist` + `tailoring` + `resume_ready`.
If that total is already ≥ target, skip search entirely — there is already enough work queued.

If the user's prompt contains a shortlist count (e.g. "stop after 10 shortlists", "find 5 jobs",
"shortlist-target 20"), extract that number and override the env var for this run only.

## Startup — open blocked job pages for manual handling

Immediately after reading the tracker (step 1 below), before launching any agents:

1. Find the first 5 `blocked` entries in the tracker that have a URL in their Notes field.
2. Open them in the background using Bash:
   ```bash
   ~/voracle-env/bin/python3 "$BROWSER_LOGIN_SCRIPT" \
     "$RESUME_OUTPUT_DIR/state/_browser/user_data" \
     '["url1","url2","url3","url4","url5"]' &
   ```
3. Print one line per URL opened:
   `[Orchestrator] 🌐 Opened for manual review: Company — Role (url)`
4. Continue immediately — do not wait for the user.

This lets the user log in and submit blocked jobs manually while the pipeline runs autonomously.

## Your responsibilities — pipeline parallelism

**Do NOT run stages sequentially.** Run all stages that have work simultaneously by calling
multiple Agent tools in the same turn. The pipeline is a conveyor belt, not a waterfall:

1. Read the tracker once at startup.
2. In a SINGLE turn, call Agent tools for every stage that has work:
   - `job-search`    if shortlist count < target
   - `resume-tailor` if tracker has any `shortlist` entries
   - `job-submitter` if tracker has any `resume_ready` or `blocked` entries
   After submitter returns, execute the generated scripts via Bash (sequential, one at a time).
3. After each agent call returns, process its output (docx conversion, relay lines, etc.),
   then immediately re-launch that agent if there is still work for it.
4. Keep all three agents running concurrently whenever possible.
5. Loop until job-search finds zero new jobs AND tailor queue is empty AND submit queue is empty.

**Never wait for search to finish before starting tailor.**
**Never wait for tailor to finish before starting submitter.**
The moment the tracker has `shortlist` entries → tailor should be running.
The moment the tracker has `resume_ready` entries → submitter should have its browser open.

**NEVER ask for confirmation before any stage — run fully autonomously.**
`blocked` entries are treated exactly like `resume_ready` — launch submitter immediately, no questions asked.
If a stage fails or produces no results, skip it and continue.
Report a brief summary after each stage completes.

## Output format

Prefix every line of output with who is speaking:

  [Orchestrator] Starting tailor stage — 85 jobs
  [Tailor] ✓ Acme Corp — Quant Developer
  [Tailor] ✗ Firm B — Risk VP  (name on line 1 didn't match source, fixed and retried)
  [Orchestrator] Tailor stage complete — 84 done, 1 error
  [Orchestrator] Converting Acme_Corp_Quant_Developer_Resume_2026.md → .docx ... ok (5 tables)
  [Orchestrator] Content check passed: name ok, all employers found, no fabrications

Rules:
- [Orchestrator] for your own planning, conversion steps, checks, and stage summaries
- [Tailor] for each result line reported back from the tailor subagent
- [Submitter] for each result line reported back from the submitter subagent
- [Search] for each result line reported back from the search subagent
- One line per job — no multi-line blocks between jobs
- Stage icons: 🎬 Orchestrator · 🔍 Search · ✂️ Tailor · 📨 Submitter — use these everywhere, never 📄 for tailor

## Critical rules — do NOT violate

- **Never check the filesystem yourself to decide whether tailoring is needed.** If the tracker has `shortlist` entries, invoke the resume-tailor subagent — always. Do not inspect `$RESUME_OUTPUT_DIR` or determine that files "already exist". That is the tailor agent's job.
- **Never mark jobs `resume_ready` yourself.** Only the tailor subagent may do this.
- **Never mark jobs `blocked` or `applied` yourself.** Only the submitter subagent may do this.

## Tracker
{WORKSPACE / "job_application_tracker.md"}
"""


async def run(prompt: str, stream: bool = True, headed: bool = True) -> str:
    env = base_env()
    env.update({
        "JOB_SEARCH_KEYWORDS":    os.environ.get("JOB_SEARCH_KEYWORDS", ""),
        "JOB_SEARCH_LOCATION":    os.environ.get("JOB_SEARCH_LOCATION", ""),
        "JOB_SEARCH_HANDOFF":     os.environ.get("JOB_SEARCH_HANDOFF", str(WORKSPACE / "SEARCH_AGENT_HANDOFF.md")),
        "JOB_SEARCH_MIN_SALARY":  os.environ.get("JOB_SEARCH_MIN_SALARY", ""),
        "JOB_SEARCH_MAX_AGE_DAYS": os.environ.get("JOB_SEARCH_MAX_AGE_DAYS", "90"),
        "JOB_SEARCH_SHORTLIST_TARGET": os.environ.get("JOB_SEARCH_SHORTLIST_TARGET", "30"),
        "USER_FIRST_NAME":  os.environ.get("USER_FIRST_NAME", ""),
        "USER_LAST_NAME":   os.environ.get("USER_LAST_NAME", ""),
        "USER_EMAIL":       os.environ.get("USER_EMAIL", ""),
        "USER_PHONE":       os.environ.get("USER_PHONE", ""),
        "USER_LINKEDIN":    os.environ.get("USER_LINKEDIN", ""),
        "RESUME_OUTPUT_DIR": os.environ.get("RESUME_OUTPUT_DIR", str(Path.home() / "Documents" / "jobs" / "tailored") + "/"),
        "RESUME_TEMPLATE":   os.environ.get("RESUME_TEMPLATE", str(SKILLS_DIR / "tailor" / "scripts" / "sample_placeholders.docx")),
        "MD_TO_DOCX_SCRIPT": os.environ.get("MD_TO_DOCX_SCRIPT", str(SKILLS_DIR / "tailor" / "scripts" / "md_to_docx.py")),
        "TRACKER_PATH":     os.environ.get("TRACKER_PATH", str(WORKSPACE / "job_application_tracker.md")),
        "SKILLS_DIR":       str(SKILLS_DIR),
        "SUBMIT_RUNNER":    str(SKILLS_DIR / "submitter" / "scripts" / "submit_runner.py"),
        "CREDENTIALS_FILE": os.environ.get("CREDENTIALS_FILE", str(WORKSPACE / "credentials.md")),
        "SEARCH_PROGRESS_LOG": str(WORKSPACE / "state" / "search_progress.log"),
        "BROWSER_LOGIN_SCRIPT": str(REPO_ROOT / "scripts" / "browser_login.py"),
        "USER_GENDER":      os.environ.get("USER_GENDER", ""),
        "USER_RACE":        os.environ.get("USER_RACE", ""),
        "USER_HISPANIC":    os.environ.get("USER_HISPANIC", ""),
        "USER_VETERAN":     os.environ.get("USER_VETERAN", ""),
        "USER_DISABILITY":  os.environ.get("USER_DISABILITY", ""),
        "USER_WORK_AUTH":   os.environ.get("USER_WORK_AUTH", ""),
        "USER_NEED_SPONSOR": os.environ.get("USER_NEED_SPONSOR", ""),
    })

    # Resolve login timeout: CLI override > tracker > default
    if os.environ.get("LOGIN_HUMAN_TIMEOUT_OVERRIDE"):
        login_timeout = int(os.environ["LOGIN_HUMAN_TIMEOUT"])
        _tracker_set_setting("login_timeout", str(login_timeout))
    else:
        saved = _tracker_get_setting("login_timeout")
        login_timeout = int(saved) if saved and saved.isdigit() else _DEFAULT_LOGIN_TIMEOUT
        os.environ.setdefault("LOGIN_HUMAN_TIMEOUT", str(login_timeout))
    env["LOGIN_HUMAN_TIMEOUT"] = str(login_timeout)

    # Seek to end of existing progress logs so we only show NEW lines from this run
    global _submit_log_pos, _search_log_pos
    resume_output_dir = os.environ.get("RESUME_OUTPUT_DIR", str(Path.home() / "Documents" / "jobs" / "tailored")).rstrip("/")
    for _log_path, _pos_var in [
        (Path(resume_output_dir) / "state" / "submit_progress.log", "_submit_log_pos"),
        (WORKSPACE / "state" / "search_progress.log",               "_search_log_pos"),
    ]:
        try:
            if _log_path.exists():
                globals()[_pos_var] = _log_path.stat().st_size
        except OSError:
            pass
    (WORKSPACE / "state").mkdir(parents=True, exist_ok=True)

    _flush_line(f"[Orchestrator] starting — may take a minute to load, please be patient...")

    result = ""
    async for message in query(
        prompt=prompt,
        options=ClaudeAgentOptions(
            cwd=str(WORKSPACE),
            allowed_tools=["Read", "Bash", "Agent"],
            system_prompt=SYSTEM_PROMPT,
            permission_mode="bypassPermissions",
            model="claude-opus-4-6",
            env=env,
            agents={
                "job-search":    search_def(headed),
                "resume-tailor": tailor_def(headed),
                "job-submitter": submitter_def(True),  # always headed — user may need to solve CAPTCHAs
            },
        ),
    ):
        if isinstance(message, AssistantMessage) and stream:
            for block in message.content:
                if isinstance(block, TextBlock):
                    _stream_text(block.text)
                elif isinstance(block, ThinkingBlock):
                    pass  # internal reasoning — not shown
                elif isinstance(block, ToolUseBlock):
                    if block.name == "Agent":
                        agent_name = block.input.get("name", "subagent")
                        _stream_text(f"[Orchestrator] → launching {agent_name}...\n")
                    elif block.name in ("Bash", "Read"):
                        pass  # too noisy to print every read/bash
        elif isinstance(message, TaskStartedMessage) and stream:
            _clear_progress()
            _stream_text(f"[task: {message.description}]\n")
        elif isinstance(message, TaskProgressMessage) and stream:
            _poll_submit_log()
            _poll_search_log()
            if message.last_tool_name:
                _show_progress(message.last_tool_name)
        elif isinstance(message, ResultMessage):
            result = message.result
            if stream:
                if _line_buf:
                    _flush_line(_line_buf)
                print()

    return result
