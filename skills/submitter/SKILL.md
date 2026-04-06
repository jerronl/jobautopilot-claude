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

Submits applications through a **code-act loop**: write actions → run runner → read page state → repeat.

## Core principles

1. **One job at a time** — finish each job before starting the next.
2. **Act on what you see** — use `page.interactive` from runner output to plan each round's selectors.
3. **Always navigate first** — round 1 must start with a `navigate` action.
4. **Don't skip fields** — every visible, unfilled required field must be addressed.
5. **Verify before marking applied** — only mark `applied` when `page.confirmed = true`.
6. **Blocked ≠ hard** — CAPTCHA and login walls need `wait_human`, not immediate `blocked`.
7. **100% truthful** — fill only from env vars and resume. Never fabricate data.

## Session start

1. Read `$JOB_SEARCH_TRACKER` — collect all `resume_ready` and `blocked` entries.
2. For each entry, note: URL (from Notes column), resume_path, cover_letter_path.
   - If path ends in `.md`, use `.docx` extension instead.
3. Process one job at a time through the loop below.

## Per-job loop

### Round 1 — Navigate and fill visible fields

Write `$RESUME_OUTPUT_DIR/state/<job_id>/round_1.json`:

```json
{
  "round": 1,
  "job_id": "<Company>_<Role>",
  "browser_state_dir": "$RESUME_OUTPUT_DIR/state/<job_id>",
  "actions": [
    {"type": "navigate", "url": "<job_url>"},
    {"type": "wait",     "ms": 2000},
    {"type": "fill",     "selector": "[name='firstName']",  "value": "<USER_FIRST_NAME>"},
    {"type": "fill",     "selector": "[name='lastName']",   "value": "<USER_LAST_NAME>"},
    {"type": "fill",     "selector": "[type='email']",      "value": "<USER_EMAIL>"},
    {"type": "fill",     "selector": "[type='tel']",        "value": "<USER_PHONE>"},
    {"type": "upload",   "selector": "input[type='file']",  "path": "<resume_path>"},
    {"type": "wait",     "ms": 500}
  ]
}
```

Run: `~/voracle-env/bin/python3 $SKILLS_DIR/submitter/scripts/submit_runner.py round_1.json`

### After each round — Analyse output

Read stdout JSON. Check:

1. **Action results** — for every `not_found`, try an alternative selector next round.
2. **page.has_login** — add `wait_human` action with reason "Login required".
3. **page.has_captcha** — add `wait_human` action with reason "CAPTCHA detected".
4. **page.confirmed** — if true → mark tracker `applied`, stop loop.
5. **page.interactive** — scan for:
   - Unfilled required inputs → fill them next round
   - Visible Submit button → click it next round
   - Visible Next/Continue → click it next round
   - Select dropdowns → use `select` action with `label` field
   - File inputs not yet uploaded → `upload` action

### Subsequent rounds

Write `round_N.json` with only the actions needed for this round:
- Fill fields that were `not_found` in previous rounds (try different selectors)
- Fill newly revealed fields from `page.interactive`
- Click Next/Submit

Stop when:
- `page.confirmed = true` → success
- `wait_human` timed out twice → mark `blocked`
- 10 rounds without progress → mark `blocked` with reason `stuck`
- `page.url` contains 404 / error page → mark `error`

## Selector fallback strategy

When a selector returns `not_found`, try in order:
1. `[name="fieldName"]`
2. `[id*="fieldName" i]`
3. `[aria-label*="field label" i]`
4. `[placeholder*="field label" i]`
5. `evaluate` action to query DOM and return matching element's selector

## Email verification codes

Many sites send a one-time code to the user's email after entering their address.
When you see a "check your email" message or a code input field after filling the email:

1. Add a `fetch_email_code` action — the runner opens a new tab, goes to Gmail/Outlook,
   searches for recent verification emails, extracts the numeric code, closes the tab.
2. The code is returned in `result.code`.
3. In the next round, `fill` the code input with that value.

```json
[
  {{"type": "fetch_email_code", "email": "$USER_EMAIL", "timeout_s": 90}},
]
```

Then in the next round:
```json
{{"type": "fill", "selector": "[name='code'], [placeholder*='code' i], [aria-label*='code' i]", "value": "<code from previous result>"}}
```

If `result.status = "code_not_found"`, add `wait_human` asking the user to check their email manually.

## EEOC fields

Read from env: `$USER_GENDER`, `$USER_RACE`, `$USER_HISPANIC`, `$USER_VETERAN`,
`$USER_DISABILITY`, `$USER_WORK_AUTH`, `$USER_NEED_SPONSOR`.

Use `select` action with `label` field for dropdowns. If env var is empty → skip.

## Cover letter

If `page.interactive` shows a textarea for cover letter, use `fill` with content
extracted from the cover letter `.docx`:

```bash
~/voracle-env/bin/python3 -c "
from docx import Document
doc = Document('<cover_letter_path>')
print('\n'.join(p.text for p in doc.paragraphs if p.text.strip()))
"
```

## Tracker update

- Loop success → `applied`, append `Applied <date>` to Notes
- CAPTCHA/login timeout → `blocked`, append reason to Notes
- Wrong URL / permanent error → `error`, append reason to Notes

## Output format (one line per job)

```
✓ Goldman Sachs — Quant Developer  (applied, 3 rounds)
✗ Citadel — Quant Risk VP  (blocked: login_required)
```

## Support

If Job Autopilot saved you time: paypal.me/ZLiu308
