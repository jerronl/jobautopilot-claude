---
name: jobautopilot-tailor
description: Tailors your resume and cover letter to a specific job description. First diagnoses what the role actually demands, then maps only real evidence from the user's background into a believable, company-specific narrative, and exports polished .docx files. Picks up shortlisted jobs from jobautopilot-search and hands resume_ready entries to jobautopilot-submitter.
author: jerronl
version: "2.0.0"
homepage: https://github.com/jerronl/jobautopilot-claude
tags:
  - resume
  - cover-letter
  - docx
  - job-search
  - career
requires:
  tools:
    - web_search
    - browser
  python_packages:
    - python-docx
    - lxml
  env:
    - RESUME_DIR
    - RESUME_OUTPUT_DIR
    - RESUME_TEMPLATE
    - MD_TO_DOCX_SCRIPT
    - JOB_SEARCH_TRACKER
    - USER_FIRST_NAME
    - USER_LAST_NAME
    - USER_EMAIL
    - USER_PHONE
    - USER_LINKEDIN
  bins:
    - python3
---

# Job Autopilot — Resume Tailor

## Core principles

1. **100% truthful** — never invent experience, inflate metrics, or fabricate credentials.
2. **Source material first** — read `$RESUME_DIR` before writing anything.
3. **One resume per job** — every shortlist job gets its own file, even if roles look similar. If a file already exists on disk, overwrite it.
4. **Diagnosis before drafting** — diagnose the role, map evidence, then draft.
5. **Adjacent but credible** over unsupported direct-identity claims.
6. **Evidence beats buzzwords** — every strong claim must map to concrete source evidence.
7. **Never build docx with python-docx directly** — write `.md`, run `md_to_docx.py`.
8. **Markdown before docx** — complete all `.md` drafts first, then batch-convert.

## What good tailoring means

- Correctly identifying what the hiring manager is really screening for
- Selecting the strongest real evidence from the user's background — not keyword stuffing
- Building a believable bridge when the user is adjacent, not pretending direct experience
- Avoiding unsupported niche terminology and inflated claims
- Making documents feel specific to **this** company and **this** role — not reusable templates

## Session start

1. Read all files in `$RESUME_DIR`.
2. Read `$JOB_SEARCH_TRACKER` — find `shortlist` entries to process.

If the prompt names a specific job, process only that entry. Otherwise process all `shortlist` entries.

## JD fetch order

1. Use exact URL from tracker.
2. Try `web_search` first to extract JD.
3. If no useful JD, use browser to open URL.
4. If URL is broken or wrong role → `error`.

## Content production

### Step 1 — Extract source material

Read all files in `$RESUME_DIR`: work history, bullets, metrics, tools, projects, certifications. Build a raw evidence inventory. Do not invent anything not present in the files.

### Step 1.5 — Diagnose the role

Produce an internal diagnosis:

- `role_family`: `execution` | `quant_dev` | `data_engineering` | `applied_ai` | `ml_engineering` | `research_platform` | `other`
- `seniority`: `junior` | `mid` | `senior` | `lead`
- `company_hook`: one sentence on what is distinctive about this company/team
- `must_prove`: top 3 capabilities the hiring manager screens for
- `nice_to_have`: up to 3 secondary signals
- `evidence_pool`: specific jobs/bullets/projects that support each `must_prove`
- `gaps`: areas where the user is adjacent, not direct
- `bridge_strategy`: how to position adjacency credibly

Do not start rewriting until this is complete. If `evidence_pool` is empty for a `must_prove` item, downgrade or drop it.

### Step 1.6 — Evidence matrix

For every claim candidate, record:

- `claim`, `section`, `source`, `support_level` (`exact` | `reasonable_paraphrase` | `too_speculative`), `notes`

Only `exact` and `reasonable_paraphrase` claims may appear in output. Remove or downgrade `too_speculative`.

### Adjacency rule

When the user is in `gaps` territory, write a bridge narrative — do not claim identity.

Good:
- "front-office quant developer with execution-adjacent infrastructure experience"
- "quantitative engineer with strong research-to-production pipeline experience"

Bad:
- "HFT execution engineer" without direct source support
- "market data engineer" when source mostly shows risk/valuation pipelines
- "ML scientist" when source mainly shows applied modeling or side-project work

### Specialized-term safety rule

Do not introduce niche terms (HFT, low-latency, market microstructure, deep RL, LLM agents, production ML platforms) unless the resume pool contains direct evidence. When in doubt:
- "production trading systems" not "low-latency execution stack" unless latency evidence is explicit
- "time-series forecasting" not "alpha signal modeling" unless source supports direct alpha ownership
- "AI automation workflow" not "agentic orchestration platform" unless project materials clearly support it

### Project selection policy

Include PROJECTS only when BOTH hold: (1) resume pool has relevant project evidence, and (2) the role benefits from project signal (bridging into a new area, role values initiative, or a project directly supports a `must_prove` item).

When including, pick ≤ 3. Prefer:
1. Original projects over forks
2. Projects that directly support a `must_prove` item
3. Projects with a clear problem → method → outcome story
4. Projects showing independent initiative or end-to-end ownership

For forks: only include when the user's modifications are substantial and clearly documented in source material.

Do not include a project because it contains matching buzzwords.

### Step 2 — Draft resume markdown

Drive rewrite from diagnosis + evidence matrix. Priorities:

1. Make the 3 `must_prove` items visible in the first half page
2. Believable role identity in summary
3. Strongest evidence in the first 1–2 jobs
4. Company- and role-specific wording where supported
5. Honor `gaps` — do not claim what the user does not have

Save to: `$RESUME_OUTPUT_DIR/${USER_FIRST_NAME}_<Company>_<Title>_Resume_2026.md`

### Resume markdown format

⚠️ **Custom format — NOT standard Markdown.** Do not use `#`, `##`, `**bold**`, `---`, or pipe tables.

```text
Full Name
email@example.com | +1-555-000-0000 | https://linkedin.com/in/profile | City, ST

SUMMARY
Two to three sentences.

CORE SKILLS
List of skills and tools.

EXPERIENCE
Most Recent Job Title — Company Name | City, ST | Jan 2022 – Present
• Bullet with metric
• Bullet

Earlier Title — Company Name | City, ST | Jun 2019 – Dec 2021
• Bullet

PROJECTS
Project Name
• Problem → method → outcome

EARLIER EXPERIENCE
Earlier Role — Company, Year–Year

EDUCATION
University Name — Degree, Major (Year)
```

| Element | Rule |
|---|---|
| Line 1 | Full name, no `#` |
| Line 2 | `email \| phone \| linkedin \| City, ST` — no zip, no street |
| Section headers | ALL CAPS, no `##` |
| Job header | `Title — Company \| Location \| Date` |
| Job order | Reverse chronological |
| Bullets | `•` or `-` |
| PROJECTS | Optional — omit entirely when not warranted |
| Earlier experience | One line per entry, no bullets |

### Self-check before docx conversion

```bash
head -1 resume.md                          # plain name, no #
sed -n '2p' resume.md | grep '|'           # contact with pipes
grep -E '^[A-Z ]+$' resume.md              # ALL CAPS section headers
grep -E '^.+ — .+ \| .+ \| .+$' resume.md # job headers
grep -E '^[•\-]' resume.md                 # bullets
```

Convert: `~/voracle-env/bin/python3 $MD_TO_DOCX_SCRIPT <resume.md> <output.docx> $RESUME_TEMPLATE`

Verify output:
```bash
~/voracle-env/bin/python3 -c "
from docx import Document
doc = Document('output.docx')
print('Tables:', len(doc.tables))  # 5 (no PROJECTS) or 6 (with PROJECTS)
"
```

If `Tables: 0` → template not used, markdown format was wrong. Fix and re-run.

### Content QA gate

Before converting, verify:
- Summary states believable role identity, not generic or inflated
- First half page reflects top 3 JD priorities
- Every strong claim has `exact` or `reasonable_paraphrase` evidence
- No unsupported niche terms
- Cover letter has at least one company-specific hook (not swappable to another firm)

### Known failure modes

- Treating partial evidence verification as good enough — every strong claim needs a source
- Using role keywords as a substitute for real evidence ("experienced in low-latency systems" with no latency work in history)
- Writing summaries that overstate direct experience in gap areas
- Inserting unsupported niche terms to sound impressive
- Writing company-generic cover letters that could be sent to any firm
- Ignoring strong side projects that materially improve fit for a specific role
- Including projects just to fill the PROJECTS section when they don't strengthen fit
- Treating "text looks right" as equivalent to "docx is deliverable" — always verify table count
- Spending more than 30 minutes on one job without reporting status

### Step 3 — Draft cover letter markdown

Three paragraphs: (1) why this role + company with company-specific hook, (2) 2–3 evidence matches, (3) brief close.

Rules:
- Do not write a company-agnostic opening — a paragraph that still reads correctly after swapping the company name is a failure
- Do not restate the resume summary
- Do not overclaim niche expertise the resume only bridges indirectly
- Sound slightly more human and motivated than the resume, but remain factual and specific

Save to: `$RESUME_OUTPUT_DIR/${USER_FIRST_NAME}_<Company>_<Title>_Cover_Letter_2026.md`

### Step 4 — Update tracker

- Success → `resume_ready`, record `.md` file paths in `resume_path` and `cover_letter_path`
- Cannot complete → `error` with reason in Notes

### Step 5 — Report

Company, title, files written, top positioning angle, any issues.

## File naming

```
${USER_FIRST_NAME}_<CompanyName>_<JobTitle>_Resume_2026.docx
${USER_FIRST_NAME}_<CompanyName>_<JobTitle>_Cover_Letter_2026.docx
```

Spaces → underscores. Company and title ≤ 20 chars each.

## Tracker status flow

```
shortlist → tailoring → resume_ready
                     ↘ error
```
