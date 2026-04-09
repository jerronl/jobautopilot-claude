# Site-specific knowledge

One file per **parent company** (not per hostname). Filename = short lowercase company slug, e.g. `blackrock.md`, `millennium.md`, `goldman_sachs.md`.

Rationale: the same employer often has multiple hostnames (`blackrock.wd1.myworkdayjobs.com`, `blackrock.wd3...`, acquired subsidiaries on different ATSes). Keying on parent company keeps related quirks in one place and avoids fragmenting knowledge across wd{1..5} subdomains. Anything that's truly ATS-wide (not employer-specific) belongs in `skills/ats_playbooks/`, not here.

## When to read

At round 1, before planning round 2:

1. Derive the company slug from `page.url` hostname (e.g. `blackrock.wd1.myworkdayjobs.com` → `blackrock`; `careers.gs.com` → `goldman_sachs`).
2. If `knowledge/sites/<slug>.md` exists, `Read` it.
3. If the file lists other hostnames under `## Hostnames`, you've confirmed the mapping. If the current hostname isn't listed, add it during the end-of-job review.

This is in addition to (not instead of) the ATS playbook lookup.

## When to write (end-of-job review only)

Append to (or create) the company file when you learn something that would save rounds next time:

- A pre-filled field the resume parser consistently mis-fills at this employer
- A required question this employer always asks, with the canonical answer
- A component/selector this employer uses that the generic ATS playbook doesn't cover
- A confirmation phrase or success URL unique to this employer
- A new hostname belonging to an existing company entry

Do NOT record things already covered by the ATS playbook — that just dilutes the file.

## Template

```markdown
# <Company Name>

**ATS:** <Workday | Oracle HCM | Eightfold | Greenhouse | Lever | custom>
**Hostnames:** `host1.example.com`, `host2.example.com`
**First seen:** YYYY-MM-DD

## Quirks

- **<date>** <one-line observation> — <selector or value if applicable>

## Canonical answers

- **Question:** "<verbatim question text>"
  **Answer:** <our answer>
  **Reason:** <why, if non-obvious>

## Known blockers

- <component/field> — <why it can't be automated; workaround if any>

## Submission confirmation

- Success URL pattern: `<regex or substring>`
- Confirmation phrase: `<text>`
```

Do not guess. Only write facts you've directly observed in a round result.
