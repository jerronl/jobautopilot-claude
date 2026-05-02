---
name: jobautopilot-search
description: "Reads your resume pool to build a candidate profile, then searches LinkedIn, Indeed, Glassdoor, ZipRecruiter, Google Jobs, and company career pages for matching roles. Filters by role, location, salary, and recency. Writes results to a structured tracker. Requires a browser tool (profile: search) and local config via environment variables. Part of the Job Autopilot pipeline."
author: jerronl
version: "1.3.3"
homepage: https://github.com/jerronl/jobautopilot-claude
tags:
  - job-search
  - linkedin
  - browser
  - career
  - tracker
requires:
  browser: true
  browser_profile: search
  env:
    - JOB_SEARCH_KEYWORDS
    - JOB_SEARCH_LOCATION
    - JOB_SEARCH_TRACKER
    - JOB_SEARCH_HANDOFF
    - RESUME_DIR
    - JOB_SEARCH_MIN_SALARY
    - JOB_SEARCH_MAX_AGE_DAYS
---

# Job Autopilot — Search Agent

## Session start

1. Read all files in `$RESUME_DIR` — build candidate profile: skills, titles, industries, seniority, location preference.
2. Read `$JOB_SEARCH_TRACKER` — note existing entries to avoid duplicates.
3. Read `$JOB_SEARCH_HANDOFF` — pick up queries run in previous sessions.

## Shortlist target

Count current `shortlist` rows in `$JOB_SEARCH_TRACKER`. If already ≥ `$JOB_SEARCH_SHORTLIST_TARGET`, stop immediately. Recount after each new shortlist decision; stop as soon as target is reached. Default target: 30.

## Search behavior

Use browser profile `search`. Primary source: LinkedIn Jobs. Also check company career pages for target employers.

Keyword combinations to try:
```
<keyword1> <keyword2> <location>
site:linkedin.com/jobs <keyword> <location>
```

Log each query in `$JOB_SEARCH_HANDOFF` to avoid repeating next session.

## Tab hygiene

If more than 10 tabs are open, close the 5 oldest before starting the next search.

## Browser crash recovery

```bash
python3 "$BROWSER_RESTART_SCRIPT" --profile search
echo "$(date +%H:%M:%S) ⚠️ Browser crashed — restarting Chromium" >> "$SEARCH_PROGRESS_LOG"
```

If MCP server itself died, continue via WebSearch/WebFetch. Write candidates to tracker as `shortlist` with `URL unverified (browser unavailable at search time)` in Notes.

## Hard filters — reject if ANY applies

- Location ≠ `$JOB_SEARCH_LOCATION` and not explicitly remote
- Posted > `$JOB_SEARCH_MAX_AGE_DAYS` days ago
- Salary listed and below `$JOB_SEARCH_MIN_SALARY`
- Role clearly junior (< 3 YOE required)
- Duplicate of existing tracker entry (same company + title)

## Tracker format

```markdown
| Company | Role | Location | Category | Posted | Salary | Status | Notes | resume_path | cover_letter_path |
|---------|------|----------|----------|--------|--------|--------|-------|-------------|-------------------|
| Acme Corp | Quant Developer | NYC | quant developer / rates | 2026-03-15 | $250k | shortlist | 3 YOE req, Python+C++. URL: https://... | | |
```

Status values: `found` | `screen_reject` | `user_reject` | `shortlist` | `tailoring` | `resume_ready` | `hold` | `applied` | `blocked` | `wrong_url` | `error`

Every kept result must include the verified final URL (after redirects) in Notes.

## Output

Print one line per job as you process it:

```
✓ Goldman Sachs — Quant Developer  (shortlisted; rates/C++/Python match; $300k; posted 3d ago)
✗ JPMorgan — Junior Analyst  (screen_reject: too junior, <3 YOE required)
```

## Handoff

After each session, update `$JOB_SEARCH_HANDOFF`: queries run, date range found, platforms or companies to revisit, anything unusual.

## Find hiring managers (user-initiated only)

Only when explicitly requested. Search LinkedIn or company website for recruiters/managers at the company. Record contacts in tracker Notes.
