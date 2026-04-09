# Site-agnostic skills / knowledge

Things that apply across employers.

## `ats_playbooks/`

Verified click / upload / multiselect sequences per ATS framework. Matched by URL pattern:

| ATS | URL pattern | File |
|-----|-------------|------|
| Workday | `*.myworkdayjobs.com` | `workday.md` |
| Oracle HCM | `*.oraclecloud.com/hcmUI/` | `oracle_hcm.md` |
| Cross-cutting selectors | (always) | `_selectors.md` |

When we verify a recipe against a new ATS (Greenhouse, Lever, Eightfold, iCIMS, SmartRecruiters, Taleo, Avature, …), add `<ats>.md` here.

## `dropdowns/`

Canonical vocabulary lists for common dropdown fields that repeat across sites.

| File | Covers |
|------|--------|
| `degrees.md` | BS / BA / MS / MBA / PhD, with common synonyms |
| `majors.md` | Computer Science, Statistics, Financial Engineering, etc. |
| `schools.md` | Universities the candidate attended, with known label variants per ATS |
| `eeoc.md` | Gender / ethnicity / race / veteran / disability standard options |
| `countries.md` | "United States" vs "United States of America" vs "USA" |

### How dropdowns are used

When the agent encounters a dropdown like "Highest Degree" or "Field of Study", it should:

1. Dump the visible options (`evaluate` over `select option` / `[role=option]` / `promptOption`).
2. `Read` the matching dropdown file.
3. Find the candidate's profile value (e.g. `Master's in Computer Science`), look up its variants in the file, and try each variant against the dumped options until one matches.
4. Select the match.
5. If none of the variants match BUT there's a clearly-equivalent option in the dump that isn't in the file yet, `Edit` the file to append the new variant under the canonical entry.

Example flow:

```
dumped = ["MS", "M.S.", "Master of Science", "MEng", "MA", "MBA", "PhD", "BS", "BA"]
profile.highest_degree = "Master's degree in Computer Science"
knowledge/skills/dropdowns/degrees.md says:
  Master of Science → ["MS", "M.S.", "Master of Science", "Masters", "Master's"]
match = "MS" (first hit in dumped)
select "MS"
```

If the dump contained `"Maîtrise"` and nothing else matched "Master of Science", agent should:
1. Decide whether Maîtrise is equivalent (yes — French for Master's)
2. Append to degrees.md: add `"Maîtrise"` to the Master of Science variants list
3. Select "Maîtrise"

### How the knowledge grows

This folder is the agent's long-term memory. Every run can add to it. The rule is: **if you just did lookup work that a future run could skip, write it down.**

### What NOT to put here

- Per-employer facts → those go in `knowledge/sites/<hostname>.md` instead
- Candidate profile data (name, email, DOB, SSN, …) → those come from env vars / credentials file, never committed here
- Ephemeral state (current round, open tabs, cookies) → those live in `~/Documents/jobs/tailored/state/`
