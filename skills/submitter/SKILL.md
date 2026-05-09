---
name: jobautopilot-submitter
description: "Submits job applications via iterative code-act loop: write actions JSON → run submit_runner.py → read page state → write next actions. Repeats until applied, blocked, or error."
author: jerronl
version: "3.0.0"
homepage: https://github.com/jerronl/jobautopilot-claude
tags:
  - job-search
  - browser-automation
  - form-filling
  - career
  - apply
requires:
  python_packages:
    - playwright
  env:
    - USER_FIRST_NAME
    - USER_LAST_NAME
    - USER_EMAIL
    - USER_PHONE
    - USER_LINKEDIN
    - RESUME_OUTPUT_DIR
    - JOB_SEARCH_TRACKER
  bins:
    - python3
---

# Job Autopilot — Submitter

## Missing dependencies

If `submit_runner.py` exits 2 and its stdout contains `"status": "missing_deps"`:

1. **Stop job processing immediately.**
2. Tell the user which dependency is missing and show the install command from `result.deps[].install`.
3. Ask the user if they would like help installing it, then stop — let Claude handle the rest.

## Session start

1. Read `$JOB_SEARCH_TRACKER` — collect all `resume_ready` and `blocked` entries.
2. For each entry: URL from Notes, resume_path, cover_letter_path. If path ends in `.md`, use `.docx`.
3. For `blocked` entries, resolve the round 1 navigate URL:
   ```bash
   bash $SKILLS_DIR/submitter/scripts/get_start_url.sh <job_id> $RESUME_OUTPUT_DIR/state/<job_id> <notes_url>
   ```
4. Process one job at a time.

## Per-job loop

### Round 1

Round 1 must always start with `navigate`. Typical starter:

```json
{
  "round": 1,
  "job_id": "<Company>_<Role>",
  "browser_state_dir": "$RESUME_OUTPUT_DIR/state/<job_id>",
  "actions": [
    {"type": "navigate", "url": "<job_url>"},
    {"type": "wait",     "ms": 2000},
    {"type": "fill",     "selector": "[name='firstName']",  "value": "$USER_FIRST_NAME"},
    {"type": "fill",     "selector": "[name='lastName']",   "value": "$USER_LAST_NAME"},
    {"type": "fill",     "selector": "[type='email']",      "value": "$USER_EMAIL"},
    {"type": "fill",     "selector": "[type='tel']",        "value": "$USER_PHONE"},
    {"type": "upload",   "selector": "input[type='file']",  "path": "<resume_path>"},
    {"type": "wait",     "ms": 500}
  ]
}
```

Run it:

```bash
python3 $SKILLS_DIR/submitter/scripts/submit_runner.py round_1.json
```

### After each round

Read stdout JSON:

1. For every `not_found` action result, try an alternative selector next round.
2. `page.has_login` → apply **Login wall strategy** (decision tree, `wait_human_login`, or Forgot Password flow). Do not use bare `wait_human` for login — it lacks auto-proceed. See agents/submitter.py "Login wall strategy" section.
3. `page.has_captcha` → add `wait_human` with reason "CAPTCHA detected". Do not immediately mark `blocked`.
4. `page.has_email_verification` → next round, use `fetch_email_code` action to extract OTP code from email. Do NOT use `wait_human` for this.
5. `page.confirmed = true` → mark `applied`, stop.
6. `page.interactive` — scan for unfilled required inputs, Submit/Next buttons, file inputs not yet uploaded.

Write `round_N.json` with only the actions needed for this round. Fill newly revealed fields, retry `not_found` selectors, click Next/Submit.

Stop when:
- `page.confirmed = true` → mark `applied`, stop
- `wait_human` timed out twice → mark `blocked`
- 5 rounds on same page/URL with no progress → emit `wait_human` (before marking `blocked`)
- 10 consecutive rounds, same URL, same failing fields → hard circuit breaker, mark `blocked: stuck` (cannot exceed)
- `page.is_generic_page = true` (round 1) → mark `wrong_url`
- `page.is_not_found = true` (round 1) → mark `expired`

**Never mark `blocked` without running round 1 first.** The tracker's existing Notes are hints from previous runs, not evidence about the current state. Prior strings like "external apply", "complex form", "account wall", "exceeds round budget", "unique ATS" do NOT permit you to emit `blocked: <reason>` before this session has executed `round_1.json` for that exact `job_id` and observed real obstacles in the runner output. Bulk-blocking many jobs in a single second is a strong signal you skipped the runner — don't.

**Before giving up on a stuck form, hand off to the human via `wait_human`.** When 5 rounds make no progress, the form has partial-fill issues you can't resolve, or you keep hitting selector errors, emit a `wait_human` action with a clear `reason` describing what you tried and what the user should do. The runner pauses up to 30 min and resumes when the user runs `touch <state_dir>/.continue` (or `touch <state_dir>/.skip` to skip). After resume, re-probe `page.interactive` — the user may have advanced the form considerably. Only mark `blocked` after the user signals skip or after two `wait_human` timeouts.

## Cover letter

If `page.interactive` shows a cover letter textarea, extract text from the `.docx` (use the tracker's `cover_letter_path` for this job) and fill it. Extract via:

```bash
python3 << 'EXTRACT_EOF'
from docx import Document
doc = Document('$cover_letter_path')
text = '\n'.join(p.text for p in doc.paragraphs if p.text.strip())
print(text)
EXTRACT_EOF
```

Capture the output and `fill` the textarea field with it.

## Selector fallback

When a selector returns `not_found`, try in order:
1. `[name="fieldName"]`
2. `[id*="fieldName" i]`
3. `[aria-label*="field label" i]`
4. `[placeholder*="field label" i]`
5. `evaluate` action to query the DOM and return the matching element's selector

## Email verification

When a "check your email" message or code input appears after filling email:

1. Add a `fetch_email_code` action — opens Gmail/Outlook tab, extracts the numeric code, closes the tab.
2. Code is returned in `result.code`.
3. Next round, `fill` the code input with that value.

```json
[{"type": "fetch_email_code", "email": "$USER_EMAIL", "timeout_s": 90}]
```

If `result.status = "code_not_found"`, add `wait_human` asking the user to check email manually.

## Pre-set answers

Fill from env vars whenever a question matches — do not skip, do not ask the user. Fall back to `wait_human` only if the env var is unset.

| Env var | Use when question contains |
|---|---|
| `$USER_GENDER` | "gender" |
| `$USER_RACE` | "race", "ethnicity" |
| `$USER_HISPANIC` | "hispanic", "latino" |
| `$USER_VETERAN` | "veteran", "military service", "protected veteran" |
| `$USER_DISABILITY` | "disability", "disabled" |
| `$USER_WORK_AUTH` | "legally authorized to work", "right to work" |
| `$USER_NEED_SPONSOR` | "require visa sponsorship", "need sponsorship" |
| `$USER_NON_COMPETE` | "non-compete", "noncompete", "restrictive covenant" |

Fill rule: `<select>` → `select` with `label`; radio → `click` matching label; checkbox → `click`.

### Default-No questions

For Yes/No questions with no env var — sanctioned countries, criminal/legal disclosures, relatives at company — default to **No** unless work history contradicts it:
- "Are you a national of Cuba/Iran/North Korea/Syria?" → No
- "Have you previously been employed by [company]?" → No (unless shown in work history)
- "Do you have relatives employed by [company]?" → No
- "Are you a referral of a client/vendor/government official?" → No

### Discovery-source

Tracker Notes contain "Found on YYYY-MM-DD via X". Extract X and match to dropdown:
- "Tech:NYC" / "jobs.technyc.org" → "Job Board" / "Tech:NYC" if listed
- "LinkedIn" → "LinkedIn"
- "Indeed" → "Indeed"
- "Company website" → "Company Website"
- Anything else → "Other" / "Other Job Board"

## Tracker update

- Applied → `applied`, append `Applied <date>` to Notes
- Blocked → `blocked`, append reason to Notes
- Wrong URL (generic page) → `wrong_url`, append reason to Notes
- Not found (404 / expired) → `expired`, append reason to Notes
- Other errors → `error`, append reason to Notes

## Output

```
✓ Goldman Sachs — Quant Developer  (applied, 3 rounds)
✗ Citadel — Quant Risk VP  (blocked: login_required)
```
