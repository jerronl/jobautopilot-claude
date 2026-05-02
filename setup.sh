#!/bin/bash
# Job Autopilot — one-time setup
# Prompts for personal info and writes ~/.jobautopilot/config.sh
set -e

# Pick up tool paths that are only set in interactive shells (.bashrc).
if [ -f "$HOME/.bashrc" ]; then
    _pnpm_home=$(grep 'PNPM_HOME=' "$HOME/.bashrc" 2>/dev/null | head -1 | sed 's/.*="\?\([^"]*\)"\?.*/\1/')
    if [ -n "$_pnpm_home" ]; then
        export PNPM_HOME="$_pnpm_home"
        export PATH="$_pnpm_home:$PATH"
    fi
fi
_nvm_dir="${NVM_DIR:-$HOME/.nvm}"
if [ -d "$_nvm_dir/versions/node" ]; then
    _node_ver=$(ls "$_nvm_dir/versions/node" | sort -V | tail -1)
    if [ -n "$_node_ver" ]; then
        export PATH="$_nvm_dir/versions/node/$_node_ver/bin:$PATH"
    fi
fi
if [ -d "$HOME/.local/bin" ]; then
    export PATH="$HOME/.local/bin:$PATH"
fi

CONFIG_DIR="$HOME/.jobautopilot"
CONFIG_FILE="$CONFIG_DIR/config.sh"
WORKSPACE="$HOME/.jobautopilot/workspace"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "============================================"
echo " Job Autopilot — Setup"
echo "============================================"
echo ""

# ── Quick environment check (fail fast before prompts) ────────────────

# Detect Python
PYTHON=""
for _cmd in python3 python; do
    if command -v "$_cmd" &>/dev/null; then
        _major=$("$_cmd" -c "import sys; print(sys.version_info.major)" 2>/dev/null)
        _minor=$("$_cmd" -c "import sys; print(sys.version_info.minor)" 2>/dev/null)
        if [ "$_major" = "3" ] && [ "${_minor:-0}" -ge 11 ]; then
            PYTHON="$_cmd"
            break
        fi
    fi
done

if [ -z "$PYTHON" ]; then
    echo "ERROR: Python 3.11+ not found."
    echo ""
    echo "  Install options:"
    echo "    Arch:   sudo pacman -S python"
    echo "    Ubuntu: sudo apt install python3"
    echo "    Mac:    brew install python"
    echo "    Other:  https://www.python.org/downloads/"
    exit 1
fi

PY_VER=$("$PYTHON" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")

# Detect pip
PIP=""
if "$PYTHON" -m pip --version &>/dev/null 2>&1; then
    PIP="$PYTHON -m pip"
else
    echo "pip not found — attempting to bootstrap..."
    if "$PYTHON" -m ensurepip --upgrade &>/dev/null 2>&1; then
        PIP="$PYTHON -m pip"
    else
        echo ""
        echo "ERROR: pip not available and could not be bootstrapped."
        echo ""
        echo "  Install options:"
        echo "    Arch:   sudo pacman -S python-pip"
        echo "    Ubuntu: sudo apt install python3-pip"
        echo "    Mac:    python3 -m ensurepip --upgrade"
        echo "  Or use a virtual environment:"
        echo "    python3 -m venv .venv && source .venv/bin/activate"
        exit 1
    fi
fi

if ! command -v npx &>/dev/null; then
    echo "ERROR: npx not found. Install Node.js and re-run."
    echo "  https://nodejs.org"
    exit 1
fi

echo "Python $PY_VER ✓   Node.js/npx ✓"
echo ""

# ── Helper functions ──────────────────────────────────────────────────
ask() {
    local prompt="$1"
    local default="$2"
    local var
    if [ -n "$default" ]; then
        read -r -p "  $prompt [$default]: " var
        echo "${var:-$default}"
    else
        read -r -p "  $prompt: " var
        echo "$var"
    fi
}

ask_secret() {
    local prompt="$1"
    local var
    read -r -s -p "  $prompt: " var
    echo "" >&2
    echo "$var"
}

# ── Install Python packages early (needed for .docx parsing below) ────
echo "Installing jobautopilot-claude..."
$PIP install -e "$SCRIPT_DIR" --quiet --disable-pip-version-check
echo ""

# ── Load existing config as defaults ─────────────────────────────────
if [ -f "$CONFIG_FILE" ]; then
    # shellcheck disable=SC1090
    source "$CONFIG_FILE" 2>/dev/null || true
    echo "(Loaded existing config from $CONFIG_FILE)"
    echo ""
fi

# ── Load existing tracker Active Search Profile as defaults ───────────
if [ -f "$WORKSPACE/job_application_tracker.md" ]; then
    _t="$WORKSPACE/job_application_tracker.md"
    _loc=$("$PYTHON" -c "
import re, pathlib
t = pathlib.Path('$_t').read_text()
m = re.search(r'- Location: (.+)', t)
print(m.group(1).strip() if m else '')
" 2>/dev/null)
    _focus=$("$PYTHON" -c "
import re, pathlib
t = pathlib.Path('$_t').read_text()
m = re.search(r'- Focus: (.+)', t)
print(m.group(1).strip() if m else '')
" 2>/dev/null)
    _comp=$("$PYTHON" -c "
import re, pathlib
t = pathlib.Path('$_t').read_text()
m = re.search(r'- Compensation: (.+)', t)
print(m.group(1).strip() if m else '')
" 2>/dev/null)
    # Tracker values override config for search fields
    [ -n "$_loc" ]   && JOB_SEARCH_LOCATION="$_loc"
    [ -n "$_focus" ] && JOB_SEARCH_KEYWORDS="$_focus"
fi

# ── Anthropic API ─────────────────────────────────────────────────────
echo "── Anthropic API ──────────────────────────────────────"
echo "  Skip if you use Claude CLI (already logged in via 'claude' command)."
API_KEY=$(ask_secret "ANTHROPIC_API_KEY (leave blank to use Claude CLI)")
[ -n "$API_KEY" ] && export ANTHROPIC_API_KEY="$API_KEY"
echo ""

# ── File paths ────────────────────────────────────────────────────────
echo "── File paths ─────────────────────────────────────────"
echo "  The agents will read your resume pool to understand your skills"
echo "  and experience before searching and tailoring."
echo ""
echo "  You can have multiple files in any name — the agents will read"
echo "  all of them. Suggested types:"
echo "    .docx / .pdf  — resume(s), include full history even if long"
echo "    .md / .txt    — skills list, certifications, side projects,"
echo "                    bio, or anything else about yourself"
echo ""
_expand() { echo "${1/#\~/$HOME}"; }
# Strip trailing slashes from existing config before using as default
RESUME_DIR="${RESUME_DIR%/}"
RESUME_OUTPUT_DIR="${RESUME_OUTPUT_DIR%/}"
RESUME_DIR=$(_expand "$(ask "Resume pool directory" "${RESUME_DIR:-~/Documents/jobs}")")
RESUME_OUTPUT_DIR=$(_expand "$(ask "Tailored output directory" "${RESUME_OUTPUT_DIR:-~/Documents/jobs/tailored}")")
# Normalize: strip any trailing slashes the user typed
RESUME_DIR="${RESUME_DIR%/}"
RESUME_OUTPUT_DIR="${RESUME_OUTPUT_DIR%/}"
echo ""

# ── Extract personal info from resume pool via Claude ─────────────────
# Seed from existing config; Claude only fills what's still missing
_R_FIRST="${USER_FIRST_NAME:-}"
_R_LAST="${USER_LAST_NAME:-}"
_R_EMAIL="${USER_EMAIL:-}"
_R_PHONE="${USER_PHONE:-}"
_R_LINKEDIN="${USER_LINKEDIN:-}"

_needs_extract=0
[ -z "$_R_FIRST" ] || [ -z "$_R_EMAIL" ] || [ -z "$_R_PHONE" ] || [ -z "$_R_LINKEDIN" ] && _needs_extract=1

if [ "$_needs_extract" -eq 0 ]; then
    echo "  (All fields already in config — skipping)"
elif ! command -v claude &>/dev/null; then
    echo "  (Skipping — claude CLI not found in PATH)"
elif [ ! -d "$RESUME_DIR" ]; then
    echo "  (Skipping — resume directory not found: $RESUME_DIR)"
elif [ -z "$(ls "$RESUME_DIR" 2>/dev/null)" ]; then
    echo "  (Skipping — resume directory is empty: $RESUME_DIR)"
else
    echo "  Reading resume pool with Claude..."

    _resume_text=$("$PYTHON" - "$RESUME_DIR" <<'PYEOF'
import sys, pathlib

resume_dir = pathlib.Path(sys.argv[1]).expanduser()
texts = []

for path in sorted(resume_dir.glob("*")):
    if path.is_dir() or path.suffix.lower() not in (".md", ".txt", ".docx", ".pdf"):
        continue
    try:
        if path.suffix.lower() in (".md", ".txt"):
            texts.append(path.read_text(errors="ignore")[:3000])
        elif path.suffix.lower() == ".docx":
            from docx import Document
            texts.append("\n".join(p.text for p in Document(str(path)).paragraphs)[:3000])
        elif path.suffix.lower() == ".pdf":
            import subprocess
            result = subprocess.run(["pdftotext", str(path), "-"], capture_output=True, text=True)
            if result.returncode == 0:
                texts.append(result.stdout[:3000])
    except Exception as e:
        import sys as _sys
        print(f"  Warning: could not read {path.name}: {e}", file=_sys.stderr)

if not texts:
    print("NO_TEXTS", end="")
else:
    print("\n\n---\n\n".join(texts)[:8000])
PYEOF
    )

    if [ "$_resume_text" = "NO_TEXTS" ]; then
        echo "  (Could not read any files from $RESUME_DIR — check file formats)"
    elif [ -n "$_resume_text" ]; then
        _tmp=$(mktemp)
        cat > "$_tmp" <<PROMPT
Extract the candidate's personal info from the resume text below.
Output ONLY these 5 lines, nothing else. If a field is not found, leave it blank after =.

FIRST_NAME=
LAST_NAME=
EMAIL=
PHONE=
LINKEDIN=

Resume text:
$_resume_text
PROMPT
        _claude_out=$(claude --print < "$_tmp" 2>/dev/null) || true
        rm -f "$_tmp"

        if [ -n "$_claude_out" ]; then
            _c_first=$(echo "$_claude_out"    | grep '^FIRST_NAME=' | cut -d= -f2-)
            _c_last=$(echo "$_claude_out"     | grep '^LAST_NAME='  | cut -d= -f2-)
            _c_email=$(echo "$_claude_out"    | grep '^EMAIL='      | cut -d= -f2-)
            _c_phone=$(echo "$_claude_out"    | grep '^PHONE='      | cut -d= -f2-)
            _c_linkedin=$(echo "$_claude_out" | grep '^LINKEDIN='   | cut -d= -f2-)
            [ -z "$_R_FIRST" ]    && _R_FIRST="$_c_first"
            [ -z "$_R_LAST" ]     && _R_LAST="$_c_last"
            [ -z "$_R_EMAIL" ]    && _R_EMAIL="$_c_email"
            [ -z "$_R_PHONE" ]    && _R_PHONE="$_c_phone"
            [ -z "$_R_LINKEDIN" ] && _R_LINKEDIN="$_c_linkedin"
        fi

        found=()
        [ -n "$_R_FIRST" ]    && found+=("name")
        [ -n "$_R_EMAIL" ]    && found+=("email")
        [ -n "$_R_PHONE" ]    && found+=("phone")
        [ -n "$_R_LINKEDIN" ] && found+=("LinkedIn")

        if [ ${#found[@]} -gt 0 ]; then
            echo "  Found: $(IFS=", "; echo "${found[*]}")"
        else
            echo "  Nothing extracted — fill in manually below."
        fi
    fi
fi
echo ""

# ── Personal info (pre-filled from resume pool) ───────────────────────
echo "── Personal info ──────────────────────────────────────"
USER_FIRST_NAME=$(ask "First name" "$_R_FIRST")
USER_LAST_NAME=$(ask "Last name" "$_R_LAST")
USER_EMAIL=$(ask "Email" "$_R_EMAIL")
_phone_label="Phone"; [ -z "$_R_PHONE" ] && _phone_label="Phone (e.g. +1-212-555-0000)"
USER_PHONE=$(ask "$_phone_label" "$_R_PHONE")
_linkedin_label="LinkedIn URL"; [ -z "$_R_LINKEDIN" ] && _linkedin_label="LinkedIn URL (e.g. https://linkedin.com/in/yourprofile)"
USER_LINKEDIN=$(ask "$_linkedin_label" "$_R_LINKEDIN")
echo ""

# ── Job search preferences ────────────────────────────────────────────
echo "── Job search preferences ─────────────────────────────"
JOB_SEARCH_KEYWORDS=$(ask "Search keywords (space-separated)" "${JOB_SEARCH_KEYWORDS:-software engineer python}")
JOB_SEARCH_LOCATION=$(ask "Target location" "${JOB_SEARCH_LOCATION:-New York City}")
JOB_SEARCH_MIN_SALARY=$(ask "Minimum annual salary in USD, numbers only (leave blank to skip)" "${JOB_SEARCH_MIN_SALARY:-}")
JOB_SEARCH_MAX_AGE_DAYS=$(ask "Max listing age in days" "${JOB_SEARCH_MAX_AGE_DAYS:-90}")
echo ""

# ── EEOC defaults ─────────────────────────────────────────────────────
echo "── EEOC defaults (US job applications) ────────────────"
echo "  These are pre-filled on forms — you'll confirm before submitting."
echo ""
USER_GENDER=$(ask "Gender" "${USER_GENDER:-Prefer not to say}")
USER_RACE=$(ask "Race/Ethnicity" "${USER_RACE:-Prefer not to say}")
USER_HISPANIC=$(ask "Hispanic or Latino? (Yes/No/Prefer not to say)" "${USER_HISPANIC:-Prefer not to say}")
USER_VETERAN=$(ask "Veteran status" "${USER_VETERAN:-I have no military service}")
USER_DISABILITY=$(ask "Disability status" "${USER_DISABILITY:-No}")
USER_WORK_AUTH=$(ask "Authorized to work in US? (Yes/No)" "${USER_WORK_AUTH:-Yes}")
USER_NEED_SPONSOR=$(ask "Require visa sponsorship? (Yes/No)" "${USER_NEED_SPONSOR:-No}")
USER_NON_COMPETE=$(ask "Bound by a non-compete agreement? (Yes/No)" "${USER_NON_COMPETE:-No}")
echo ""

# ── Write config ──────────────────────────────────────────────────────
# jobautopilot CLI is installed alongside the Python executable (same bin/)
_JA_BIN_DIR="$(dirname "$($PYTHON -c 'import sys; print(sys.executable)')")"

mkdir -p "$CONFIG_DIR"
cat > "$CONFIG_FILE" <<EOF
#!/bin/bash
# Job Autopilot — personal configuration
# Generated by setup.sh on $(date)

# ── CLI path ─────────────────────────────────────────────────────────
export PATH="$_JA_BIN_DIR:\$PATH"

# ── Anthropic API (leave unset to use Claude CLI auth) ───────────────
${API_KEY:+export ANTHROPIC_API_KEY="$API_KEY"}

# ── Personal info ────────────────────────────────────────────────────
export USER_FIRST_NAME="$USER_FIRST_NAME"
export USER_LAST_NAME="$USER_LAST_NAME"
export USER_EMAIL="$USER_EMAIL"
export USER_PHONE="$USER_PHONE"
export USER_LINKEDIN="$USER_LINKEDIN"

# ── File paths ───────────────────────────────────────────────────────
export RESUME_DIR="$RESUME_DIR"
export RESUME_OUTPUT_DIR="$RESUME_OUTPUT_DIR"

# ── Job search ───────────────────────────────────────────────────────
export JOB_SEARCH_KEYWORDS="$JOB_SEARCH_KEYWORDS"
export JOB_SEARCH_LOCATION="$JOB_SEARCH_LOCATION"
export JOB_SEARCH_MIN_SALARY="$JOB_SEARCH_MIN_SALARY"
export JOB_SEARCH_MAX_AGE_DAYS="$JOB_SEARCH_MAX_AGE_DAYS"

# ── EEOC defaults ────────────────────────────────────────────────────
export USER_GENDER="$USER_GENDER"
export USER_RACE="$USER_RACE"
export USER_HISPANIC="$USER_HISPANIC"
export USER_VETERAN="$USER_VETERAN"
export USER_DISABILITY="$USER_DISABILITY"
export USER_WORK_AUTH="$USER_WORK_AUTH"
export USER_NEED_SPONSOR="$USER_NEED_SPONSOR"
export USER_NON_COMPETE="$USER_NON_COMPETE"
EOF
chmod 600 "$CONFIG_FILE"

# ── Initialize workspace & resume dirs ───────────────────────────────
mkdir -p "$WORKSPACE"
mkdir -p "$RESUME_DIR"
mkdir -p "$RESUME_OUTPUT_DIR"

TRACKER="$WORKSPACE/job_application_tracker.md"
if [ ! -f "$TRACKER" ]; then
    # First run — create full tracker
    cat > "$TRACKER" <<TRACKER_EOF
# Job Application Tracker

## Active Search Profile

- Location: $JOB_SEARCH_LOCATION
- Focus: $JOB_SEARCH_KEYWORDS
- Compensation: ${JOB_SEARCH_MIN_SALARY:+\$${JOB_SEARCH_MIN_SALARY}+}${JOB_SEARCH_MIN_SALARY:-not specified}

## Status Legend

- \`found\` = discovered, not yet reviewed
- \`screen_reject\` = filtered out in rough screening
- \`user_reject\` = rejected after user review
- \`shortlist\` = approved for resume tailoring
- \`tailoring\` = resume/cover letter in progress
- \`resume_ready\` = docx files ready, waiting to submit
- \`applied\` = submitted
- \`hold\` = paused, revisit later
- \`wrong_url\` = URL is a generic page or broken
- \`error\` = something went wrong

## Settings

| Key | Value |
|-----|-------|
| login_timeout | 60 |

## Jobs

| Company | Role | Location | Category | Posted | Salary | Status | Notes | resume_path | cover_letter_path |
|---------|------|----------|----------|--------|--------|--------|-------|-------------|-------------------|
TRACKER_EOF
else
    # Re-run — only update Active Search Profile, leave job data intact
    "$PYTHON" - "$TRACKER" "$JOB_SEARCH_LOCATION" "$JOB_SEARCH_KEYWORDS" "${JOB_SEARCH_MIN_SALARY:-}" <<'PYEOF'
import sys, re, pathlib

tracker = pathlib.Path(sys.argv[1])
location, focus, salary = sys.argv[2], sys.argv[3], sys.argv[4]
comp = f"${salary}+" if salary else "not specified"

text = tracker.read_text()
text = re.sub(r'(## Active Search Profile\n)(.*?)(\n## )',
    f'\\1\n- Location: {location}\n- Focus: {focus}\n- Compensation: {comp}\n\\3',
    text, flags=re.DOTALL)
tracker.write_text(text)
PYEOF
fi

CREDENTIALS="$WORKSPACE/credentials.md"
if [ ! -f "$CREDENTIALS" ]; then
    cat > "$CREDENTIALS" <<'CREDS_EOF'
# Job Site Credentials
<!-- Auto-maintained by Job Autopilot submitter agent -->

| Site | Email | Password | Date |
|------|-------|----------|------|
CREDS_EOF
fi

HANDOFF="$WORKSPACE/SEARCH_AGENT_HANDOFF.md"
if [ ! -f "$HANDOFF" ]; then
    cat > "$HANDOFF" <<'HANDOFF_EOF'
# Search Agent Handoff

Notes carried between search sessions (queries run, date ranges, platforms visited).
HANDOFF_EOF
fi

echo "Config saved → $CONFIG_FILE"
echo ""

# ── Install Playwright browsers (slow part) ───────────────────────────
echo "============================================"
echo " Installing browsers..."
echo "============================================"
echo ""

echo "[1/1] Playwright browsers..."
if ls ~/.cache/ms-playwright/chromium-* 2>/dev/null | grep -q chromium; then
    echo "      Already installed, skipping."
else
    echo "      Downloading (~200MB, one-time)..."
    npx playwright install chromium 2>/dev/null && echo "      Done." || \
        echo "      (Will be downloaded on first run)"
fi

# ── Browser test ─────────────────────────────────────────────────────
echo ""
echo "Testing browser..."
_browser_ok=0

# Find a browser to test with
_browser_bin=""
for _b in chromium chromium-browser google-chrome; do
    command -v "$_b" &>/dev/null && _browser_bin="$_b" && break
done

if [ -z "$_browser_bin" ]; then
    echo "  WARNING: No browser found to test."
    echo "  Install chromium: sudo pacman -S chromium (Arch) or sudo apt install chromium (Ubuntu)"
elif [ -z "$DISPLAY" ] && [ -z "$WAYLAND_DISPLAY" ]; then
    echo "  WARNING: No display detected (\$DISPLAY and \$WAYLAND_DISPLAY are unset)."
    echo "  Browser automation will not work without a display."
    echo ""
    echo "  On WSL2, make sure WSLg is running (Windows 11) or set up an X server."
else
    # Launch browser briefly and check if it opens
    DISPLAY="${DISPLAY:-:0}" "$_browser_bin" --no-sandbox --headless=new about:blank \
        2>/dev/null &
    _bpid=$!
    sleep 3
    if kill -0 "$_bpid" 2>/dev/null; then
        kill "$_bpid" 2>/dev/null
        _browser_ok=1
        echo "  Browser OK ✓"
    else
        echo "  WARNING: Browser launched but exited immediately."
    fi
fi

if [ "$_browser_ok" -eq 0 ] && [ -n "$_browser_bin" ]; then
    echo ""
    echo "  Browser test failed. Job search and form submission require a working browser."
    echo ""
    if command -v claude &>/dev/null; then
        read -r -p "  Open Claude to help diagnose the browser issue? [Y/n]: " _ans
        if [ "${_ans:-Y}" != "n" ] && [ "${_ans:-Y}" != "N" ]; then
            claude "Help me fix browser display issues on $(uname -a). \
DISPLAY=$DISPLAY WAYLAND_DISPLAY=$WAYLAND_DISPLAY. \
I'm trying to run headed Chromium for browser automation (Playwright MCP) \
but the browser window doesn't appear or the browser exits immediately. \
What should I check and fix?"
        fi
    else
        echo "  Tip: Run 'claude \"Help me fix browser display on WSL2\"' after installing Claude CLI."
    fi
fi

# ── Browser login for job sites (one-time) ───────────────────────────
echo ""
echo "============================================"
echo " Job site login (one-time)"
echo "============================================"
echo ""
echo "Two browser profiles need to be logged in separately:"
echo "  1. Search browser  — for browsing job listings (LinkedIn, eFinancialCareers, etc.)"
echo "  2. Submit browser  — for submitting applications + your webmail"
echo ""
echo "The submit browser also opens your webmail so the submitter can fetch"
echo "password-reset links and verification codes for ATS portals (Workday, Oracle,"
echo "eFinancialCareers, etc.) that require an account."
echo ""

_SEARCH_PROFILE="$HOME/.jobautopilot/browser_profiles/search"
_SUBMIT_PROFILE="$HOME/.jobautopilot/browser_profiles/submit"
mkdir -p "$_SEARCH_PROFILE" "$_SUBMIT_PROFILE"

_JOB_SITES=(
    "https://www.linkedin.com/login"
    "https://www.efinancialcareers.com/"
    "https://www.indeed.com/account/login"
)

# Find Playwright's Chromium (shared between Node.js and Python playwright)
_pw_chromium=$("$PYTHON" -c "
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    print(p.chromium.executable_path)
" 2>/dev/null)

# Guess webmail URL from email domain
_webmail_url=""
if [ -n "$USER_EMAIL" ]; then
    _domain="${USER_EMAIL##*@}"
    case "${_domain,,}" in
        gmail.com)                          _webmail_url="https://mail.google.com/" ;;
        outlook.com|hotmail.com|live.com|\
        msn.com|outlook.*|hotmail.*)        _webmail_url="https://outlook.live.com/mail/" ;;
        yahoo.com|yahoo.*)                  _webmail_url="https://mail.yahoo.com/" ;;
        icloud.com|me.com|mac.com)          _webmail_url="https://www.icloud.com/mail/" ;;
        proton.me|protonmail.com)           _webmail_url="https://mail.proton.me/" ;;
        aol.com)                            _webmail_url="https://mail.aol.com/" ;;
        *)                                  _webmail_url="https://mail.$_domain/" ;;
    esac
fi

_SUBMIT_SITES=("${_JOB_SITES[@]}")
if [ -n "$_webmail_url" ]; then
    _SUBMIT_SITES+=("$_webmail_url")
fi

_SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
_LOGIN_SCRIPT="$_SCRIPT_DIR/scripts/browser_login.py"

_make_json() {
    local sites_json="["
    local first=1
    for url in "$@"; do
        if [ "$first" -eq 0 ]; then sites_json+=","; fi
        sites_json+="\"$url\""
        first=0
    done
    echo "${sites_json}]"
}

if [ -n "$_LOGIN_SCRIPT" ] && \
   { [ -n "$DISPLAY" ] || [ -n "$WAYLAND_DISPLAY" ]; }; then
    # Wipe profiles — fresh login, removes stale locks and corrupted state
    rm -rf "$_SEARCH_PROFILE" "$_SUBMIT_PROFILE" 2>/dev/null || true
    mkdir -p "$_SEARCH_PROFILE" "$_SUBMIT_PROFILE"

    echo "Opening Search browser (window 1)..."
    DISPLAY="${DISPLAY:-:0}" "$PYTHON" "$_LOGIN_SCRIPT" \
        "$_SEARCH_PROFILE" "$(_make_json "${_JOB_SITES[@]}")" &
    _bpid1=$!

    sleep 3  # let browser 1 claim its singleton socket first

    echo "Opening Submit browser (window 2)..."
    DISPLAY="${DISPLAY:-:0}" "$PYTHON" "$_LOGIN_SCRIPT" \
        "$_SUBMIT_PROFILE" "$(_make_json "${_SUBMIT_SITES[@]}")" &
    _bpid2=$!

    sleep 3
    echo ""
    echo "Both browsers are open."
    echo "  Window 1 — Search:  LinkedIn, eFinancialCareers, Indeed"
    _submit_desc="LinkedIn, eFinancialCareers, Indeed"
    if [ -n "$_webmail_url" ]; then
        _mail_host=$(echo "$_webmail_url" | sed 's|https\?://\([^/]*\).*|\1|')
        _submit_desc="$_submit_desc, $_mail_host (for password resets)"
    fi
    echo "  Window 2 — Submit:  $_submit_desc"
    echo ""
    echo "Log in to all tabs. The submitter will use your webmail to fetch"
    echo "password-reset links for ATS portals it encounters during applications."
    echo ""

    _reply=""
    while [ "$_reply" != "done" ]; do
        read -r -p "  Log in to all tabs, then type 'done' and press Enter: " _reply </dev/tty
    done

    kill "$_bpid1" "$_bpid2" 2>/dev/null || true
    wait "$_bpid1" "$_bpid2" 2>/dev/null || true
    echo "  Saved ✓"
else
    if [ -z "$_pw_chromium" ]; then
        echo "  (Skipping — Playwright Chromium not installed yet)"
        echo "  Run 'npx playwright install chromium' then re-run setup.sh to log in."
    else
        echo "  (Skipping — no display detected)"
        echo "  On first run, each agent will prompt you to log in."
    fi
fi

# ── Done ──────────────────────────────────────────────────────────────
echo ""
echo "============================================"
echo " Setup complete!"
echo "============================================"
echo ""
echo "Resume pool: $RESUME_DIR/"
echo ""
echo "── How to run ─────────────────────────────────────────"
echo ""
echo "  Load your config first (once per terminal session):"
echo "    source $CONFIG_FILE"
echo ""
echo "  Tell the orchestrator what to do:"
echo "    jobautopilot \"Search for $JOB_SEARCH_KEYWORDS jobs in $JOB_SEARCH_LOCATION\""
echo "    jobautopilot \"Tailor resumes for shortlisted jobs\""
echo "    jobautopilot \"Submit all resume_ready applications\""
echo "    jobautopilot \"Submit all blocked jobs\"   # retry previously blocked"
echo ""
echo "  Or run the full pipeline (search + tailor + submit run concurrently):"
echo "    jobautopilot \"Run the full pipeline\""
echo ""
echo "  Check your inbox and auto-update tracker (rejections, interviews, OA"
echo "  invites). Uses the submitter's already-signed-in browser, no OAuth:"
echo "    jobautopilot \"Check my email for anything job-related I need to handle\""
echo ""
echo "  Press Ctrl+C at any time to stop."
echo ""
