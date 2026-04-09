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
metadata:
  clawdbot:
    emoji: "📄"
    requires:
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
      pip:
        - python-docx
        - lxml
    files:
      - scripts/md_to_docx.py
---

# Job Autopilot — Resume Tailor

Produces a tailored resume and cover letter for each `shortlist` job in the tracker. Delivers `.docx` files ready to attach and send.

## What "good tailoring" means

Good tailoring is **not** keyword stuffing and **not** pretending the user has done a job they only partially match.

Good tailoring means:

- correctly identifying what the hiring manager is really screening for
- selecting the strongest real evidence from the user's resume pool and projects
- building a believable bridge when the user is adjacent to the role rather than a perfect match
- avoiding unsupported niche terminology and inflated claims
- making the final documents feel specific to **this** company and **this** role, not reusable templates

## Core principles

1. **100% truthful** — never invent experience, inflate metrics, fabricate credentials, or imply direct ownership where the source material only shows adjacency.
2. **Source material first** — always read `$RESUME_DIR` before writing anything. Resume content must come from the user's original files and clearly grounded project evidence.
3. **One resume per job, no exceptions** — every `shortlist` job gets its own dedicated resume and cover letter file. Never group jobs into archetypes. Never reuse a finished file across multiple jobs, even if the roles look similar. If a file already exists on disk for a `shortlist` job, overwrite it.
4. **Diagnosis before drafting** — never start rewriting from raw keyword matching. First diagnose the role, then map evidence, then draft.
5. **Believable bridge over fake identity** — for specialized roles, prefer "adjacent but credible" language over unsupported direct-identity claims.
6. **Evidence beats buzzwords** — every strong claim in summary, skills, experience, and projects must map to concrete source evidence.
7. **Projects are real evidence, not decoration** — actively evaluate side projects and GitHub work when they materially improve fit. Skip the PROJECTS section entirely when the resume pool has no relevant projects or the role does not benefit from them.
8. **Never build a resume docx with python-docx directly** — the only permitted way to produce a resume `.docx` is: write a `.md` file in the exact custom format, then run `md_to_docx.py` with the template. Building the resume from scratch with `python-docx` is forbidden because it breaks template formatting.
9. **Markdown before docx** — complete markdown drafts for all targeted jobs first, then convert to docx in batch. Do not interleave writing and conversion.
10. **One job at a time for reporting** — finish and report each job's result before moving to the next.
11. **No silent spinning** — if a job cannot be reliably completed within 30 minutes, mark it `error` with a clear reason and move on.

## Setup

Add to `~/.jobautopilot/config.sh`:

```bash
export RESUME_DIR="$HOME/Documents/jobs/"
export RESUME_OUTPUT_DIR="$HOME/Documents/jobs/tailored/"
export RESUME_TEMPLATE="/path/to/jobautopilot-claude/skills/tailor/scripts/sample_placeholders.docx"
export MD_TO_DOCX_SCRIPT="/path/to/jobautopilot-claude/skills/tailor/scripts/md_to_docx.py"
export JOB_SEARCH_TRACKER="$HOME/.jobautopilot/workspace/job_application_tracker.md"
export USER_FIRST_NAME="Your"
export USER_LAST_NAME="Name"
export USER_EMAIL="your@email.com"
export USER_PHONE="+1-555-000-0000"
export USER_LINKEDIN="https://linkedin.com/in/yourprofile"
mkdir -p "$RESUME_OUTPUT_DIR"
```

## Session start

Read in order:

1. `$RESUME_DIR` — understand the user's full experience, tools, assets, projects, and previous tailoring patterns
2. `$JOB_SEARCH_TRACKER` — find the job(s) to process

If the prompt specifies a single job, process only that entry. If no specific job is named, process all `shortlist` entries.

## JD fetch order

For each shortlist job:

1. Use the exact URL from the tracker
2. Try `web_search` first to extract job responsibilities, skills, keywords, asset classes, product scope, team context, and company-specific hooks
3. If `web_search` returns no useful JD, use browser to open the URL directly
4. If the URL is broken, a generic careers page, or wrong role, mark tracker `error` and explain why

## Content production order

For each job, strictly in this sequence:

### Step 1 — Read and extract source material

Read all files in `$RESUME_DIR`. The pool may contain:

| File type                          | What to extract                                                      |
| ---------------------------------- | -------------------------------------------------------------------- |
| Master resume (`.docx` / `.pdf`)   | Full work history, bullets, metrics, dates, tools, products, systems |
| Older tailored versions            | Strong phrasing that remains truthful and role-appropriate           |
| Cover letter drafts                | Preferred voice, opening formulas, recurring themes                  |
| Skills list / bio (`.md` / `.txt`) | Certifications, tools, side projects, publications                   |
| Project notes / GitHub summaries   | Side projects, methods used, end-user outcomes, technical stacks     |

Extract everything factual. Build a raw evidence inventory containing: companies, titles, dates, tools/languages, asset classes, methods/models, systems built or supported, users/stakeholders, metrics and scale indicators, side projects and patents if present.

Do not invent anything not present in the files or clearly linked project evidence.

### Step 1.5 — Diagnose the role before tailoring

Before writing any resume or cover letter content, produce an internal role diagnosis with these fields:

- `role_family`: one of `execution`, `quant_dev`, `data_engineering`, `applied_ai`, `ml_engineering`, `research_platform`, `other`
- `seniority`: `junior`, `mid`, `senior`, `lead`
- `company_hook`: one sentence on what is distinctive about this company/team from the JD
- `must_prove`: the top 3 capabilities the hiring manager is likely screening for
- `nice_to_have`: up to 3 secondary signals that would strengthen fit
- `evidence_pool`: specific jobs, bullets, projects, or files from `$RESUME_DIR` that support each `must_prove` item
- `gaps`: the main missing areas where the user is only adjacent, not direct — these dictate what NOT to claim and where bridge language is required
- `bridge_strategy`: how to position adjacency credibly without pretending direct experience

Do not start rewriting until this diagnosis is complete.

If `evidence_pool` is empty for a `must_prove` item, downgrade or drop that item. Never fill a gap with invented language.

### Step 1.6 — Build an evidence matrix

Create an internal evidence matrix before drafting.

For every claim candidate you may want to use in the tailored documents, record:

- `claim`
- `section`: summary / skills / experience / project / cover_letter
- `source`
- `support_level`: `exact`, `reasonable_paraphrase`, or `too_speculative`
- `notes`

Rules:

- Only `exact` and `reasonable_paraphrase` claims may appear in output
- `too_speculative` claims must be removed or downgraded
- The more niche, senior, or specialized a term is, the stronger the evidence required

### Evidence mapping rule

Every strong claim in SUMMARY, CORE SKILLS, EXPERIENCE, PROJECTS, and the cover letter must map to at least one concrete source fact.

Examples:

- Allowed: "built Python modules for batch risk generation" when source clearly states that
- Allowed: "research-to-production turnaround" when the source clearly shows fast translation from models to production
- Not allowed: "HFT execution engineer" if the user only has execution-adjacent infrastructure experience
- Not allowed: "market microstructure expert" if source does not show order-book or execution-quality work

### Adjacency rule for specialized roles

When the user is in `gaps` territory for the target role, write a bridge narrative instead of pretending identity.

Good:

- "front-office quant developer with execution-adjacent infrastructure experience"
- "quantitative engineer with strong research-to-production pipeline experience"
- "data engineer with deep quantitative analytics background"

Bad:

- "HFT execution engineer" without direct source support
- "market data engineer" when the source mostly shows risk/valuation data pipelines
- "ML scientist" when the source mainly shows applied modeling or side-project work

### Specialized-term safety rule

For niche roles such as HFT, low-latency systems, market microstructure, deep RL, LLM agents, or production ML platforms:

- do not introduce specialized terms unless the resume pool contains direct evidence or a clearly adjacent supporting fact
- if a JD term is attractive but unsupported, either omit it or rewrite at a more defensible abstraction level
- when in doubt, a believable bridge beats an unsupported buzzword

Examples:

- Prefer "production trading systems" over "low-latency execution stack" unless low-latency evidence is explicit
- Prefer "time-series forecasting" over "alpha signal modeling" unless source supports direct alpha ownership
- Prefer "AI automation workflow" over "agentic orchestration platform" unless the project materials clearly support that wording

### Project selection policy

Projects are **optional**. Include a PROJECTS section only when BOTH conditions hold:
1. The resume pool actually contains relevant project evidence
2. The role meaningfully benefits from project signal (e.g., the user is bridging into a new area, the role values independent initiative, or a project directly supports a `must_prove` item)

When including PROJECTS, pick up to 3 projects. Prefer:

1. original projects over forks
2. projects that directly support a `must_prove` item
3. projects with a clear problem → method → outcome story
4. projects that show independent initiative or end-to-end ownership

Do not include a project just because it contains matching buzzwords.

For each included project, state:

- the problem solved
- the method / system built
- the end-user, production, or workflow outcome

If a project is a fork, only include it when the user's modifications are substantial and clearly documented in the source material.

When the conditions above are not met, omit the entire PROJECTS section from the markdown — `md_to_docx.py` will automatically remove the PROJECTS table and all unused PROJ placeholders from the output docx.

### Resume markdown format specification

⚠️ **This is NOT standard Markdown.** `md_to_docx.py` uses a custom line-based parser. Standard Markdown headings (`#`, `##`, `###`), bold (`**text**`), horizontal rules (`---`), and pipe tables will all silently break parsing. Do not use any of those constructs.

**WRONG — standard Markdown (do not use):**

```text
# Jane Doe
**New York | jane@example.com**
---
## SUMMARY
...
### Associate Director | DTCC
**New York, NY | 2024–Present**
- bullet
```

**CORRECT — custom format required by md_to_docx.py:**

```text
Full Name
email@example.com | +1-555-000-0000 | https://linkedin.com/in/profile | City, ST

SUMMARY
Two to three sentences summarizing the candidate.

CORE SKILLS
List of skills, tools, and technologies relevant to this role.

EXPERIENCE
Most Recent Job Title — Company Name | City, ST | Jan 2022 – Present
• Accomplished X by doing Y, resulting in Z
• Another bullet point with a metric

Second Most Recent Title — Company Name | City, ST | Jun 2019 – Dec 2021
• Bullet point
• Bullet point

PROJECTS
Project Name
• Problem solved, method used, outcome achieved
• Additional detail if needed

Another Project
• Problem → method → outcome

EARLIER EXPERIENCE
Earlier Role — Company, Year–Year
Another Earlier Role — Company, Year–Year

EDUCATION
University Name — Degree, Major (Year)
```

**Parsing rules the script enforces — follow these exactly:**

| Element            | Rule                                                                                                                                          |
| ------------------ | --------------------------------------------------------------------------------------------------------------------------------------------- |
| Line 1             | Full name, plain text, no `#` heading marker                                                                                                  |
| Line 2             | Contact info, pipe-separated: `email \| phone \| linkedin_url \| City, ST` — no zip codes, no street address                                  |
| Section headers    | ALL CAPS, no `##` — exactly `SUMMARY`, `CORE SKILLS`, `EXPERIENCE`, `PROJECTS` (optional), `EARLIER EXPERIENCE`, `EDUCATION`                  |
| Job header         | `Title — Company \| Location \| Date range` — separator is ` — ` (em dash with spaces), fields separated by ` \| `                            |
| Job order          | **Reverse chronological — most recent job first**                                                                                             |
| Bullets            | Start with `•` or `-`, one per line                                                                                                           |
| Project header     | Single line, just the project name (no `—`, no `\|`). Followed by `•`/`-` bullets                                                             |
| PROJECTS section   | **Optional.** Omit entirely when not warranted — the script removes the PROJECTS table and all unused placeholders automatically              |
| Earlier experience | **One line per entry, no bullets**: `Role — Company, Year–Year`                                                                               |
| Education          | One line per entry: `University — Degree`                                                                                                     |

**What the script handles automatically:**
- More jobs/projects than template slots → clones the last item's formatting
- Fewer jobs/projects than template slots → removes unused placeholders
- No PROJECTS section in markdown → removes the entire PROJECTS table from docx
- Same logic for bullets, earlier experience, and education entries

### Step 2 — Draft the resume markdown

Drive the rewrite from the Step 1.5 diagnosis and Step 1.6 evidence matrix, not from raw keyword matching.

Priorities:

1. Make the 3 `must_prove` items visible in the first half page
2. Build a believable role identity in the summary
3. Surface the strongest supporting evidence in the first 1–2 jobs
4. Use company- and role-specific wording where supported
5. Honor `gaps` — do not claim what the user does not have
6. Prefer precise, grounded phrasing over impressive but risky wording

The summary may state at most 2–3 of the strongest, most defensible positioning angles. Do not use the summary to preload capabilities the body cannot support.

If the role is specialized and the user is only adjacent, explicitly tailor toward adjacency, not identity.

Save to: `$RESUME_OUTPUT_DIR/${USER_FIRST_NAME}_<Company>_<Title>_Resume_2026.md`

### Self-check before converting to docx

Before running `md_to_docx.py`, verify the markdown against these rules:

```bash
# Line 1 must be plain name (no # prefix)
head -1 resume.md

# Line 2 must contain pipes (contact info)
sed -n '2p' resume.md | grep '|'

# Section headers must be ALL CAPS with no ## prefix
grep -E '^[A-Z ]+$' resume.md

# Job headers must match: Title — Company | Location | Date
grep -E '^.+ — .+ \| .+ \| .+$' resume.md

# Bullets must start with • or -
grep -E '^[•\-]' resume.md
```

If any check fails, fix the markdown before proceeding.

**After running md_to_docx.py, verify the output docx has the correct structure:**

```bash
~/voracle-env/bin/python3 - << 'EOF'
from docx import Document
doc = Document("output.docx")
print("Tables:", len(doc.tables))   # 5 (no PROJECTS) or 6 (with PROJECTS)
print("Paras:", len(doc.paragraphs))
EOF
```

If `Tables: 0`, the template was not used — the markdown format was wrong. Fix the .md and re-run. Do NOT proceed with a docx that has 0 tables.

### Content QA gate

Before converting markdown to docx, verify ALL of the following. If any check fails, revise the markdown.

- The summary states a believable role identity, not a generic one and not an inflated one
- The first half page clearly reflects the top 3 JD priorities from the diagnosis
- Every strong claim has source evidence classified as `exact` or `reasonable_paraphrase`
- No specialized or niche terms were introduced without support
- The wording sounds like this user, not a generic senior engineer template
- If you replaced the company name with another firm in the same family, the document would **not** still fit unchanged
- For specialized roles, the resume shows domain-specific evidence rather than generic synonyms
- The document highlights differentiators that actually matter for this role, including projects when appropriate
- If PROJECTS section is present, every listed project genuinely strengthens fit (not buzzword padding); if absent, that decision was deliberate

### Step 3 — Draft the cover letter markdown

Three paragraphs max:

1. Why this role + company — **must include at least one company-specific hook** drawn from the JD, business model, asset focus, product scope, research style, or execution model. A paragraph that would still read correctly after swapping the company name is a failure.
2. Most relevant evidence match — 2 to 3 specific points tied to source evidence
3. Brief close

Rules:

- Do not write a company-agnostic opening
- Do not simply restate the summary from the resume
- Do not overclaim niche expertise that the resume itself only bridges indirectly
- The cover letter should sound slightly more human and motivated than the resume, but remain factual and specific

Save to: `$RESUME_OUTPUT_DIR/${USER_FIRST_NAME}_<Company>_<Title>_Cover_Letter_2026.md`

### Step 4 — Update tracker

- Success → `resume_ready`, record the markdown file paths in `resume_path` and `cover_letter_path`
- Cannot complete → `error`, write a clear reason in Notes

### Step 5 — Report

Report:

- company
- title
- files written
- top positioning angle used
- any issues or confidence warnings

## File naming convention

```
${USER_FIRST_NAME}_<CompanyName>_<JobTitle>_Resume_2026.docx
${USER_FIRST_NAME}_<CompanyName>_<JobTitle>_Cover_Letter_2026.docx
```

Spaces → underscores. Keep company and title short (≤ 20 chars each if possible).

## Tracker status flow

```
shortlist → tailoring → resume_ready
                     ↘ error
```

## Known failure modes to avoid

- treating partial verification as good enough
- using role keywords as a substitute for real evidence
- writing summaries that overstate direct experience
- inserting unsupported niche terms to sound impressive
- writing company-generic cover letters
- ignoring strong side projects that materially improve fit
- including projects just to fill the section when they don't strengthen fit
- treating "text looks right" as equivalent to "docx is deliverable"
- spending more than 30 minutes on one job without reporting status

## Scope

Resume tailoring only. Do not submit applications. Hand off `resume_ready` entries to the `jobautopilot-submitter` skill.

## Support

If Job Autopilot saved you time: paypal.me/ZLiu308
