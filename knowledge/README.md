# knowledge/

Persistent, growing knowledge base for the submitter/tailor/search agents.
Two top-level folders:

## `sites/`

**Site-specific** notes — one file per domain (e.g. `blackrock.wd1.myworkdayjobs.com.md`, `career.mlp.com.md`, `linkedin.com.md`). Records quirks that only apply to one employer's portal:
- Which pre-filled fields the resume parser gets wrong
- Which questions this employer always asks (and canonical answers)
- Login quirks (SSO path, 2FA flow, session timeout)
- Known-blocker components that can't be automated on this site
- Submit confirmation selector / success URL pattern for this portal

**Filename**: use the hostname as-is (`blackrock.wd1.myworkdayjobs.com.md`), not a friendly name. This makes lookup deterministic from `new URL(page.url).hostname`.

Agents should **Read** the matching file at round 1 if it exists, and **Edit/append** new quirks as they discover them — the bot improves itself over time.

## `skills/`

**Site-agnostic** knowledge that applies across employers. Currently:

- `ats_playbooks/` — verified click/upload/multiselect sequences per ATS framework (Workday, Oracle HCM, …) plus cross-cutting CSS/selector rules. Matched by URL pattern.
- `dropdowns/` — canonical vocabularies for common dropdown fields (schools, majors, degrees, EEOC options, countries). When the form has a dropdown for "University", the agent looks up candidate variants here first (e.g. `"University of Illinois at Urbana-Champaign"` vs `"UIUC"` vs `"Univ of Illinois Urbana Champaign"`) and tries them before giving up.

When an agent discovers a new dropdown label variant that wasn't in the vocab file, it should **append** the variant so future runs recognize it. This is how the knowledge base grows.

## Read / write protocol

- **Read** a knowledge file at the moment it becomes relevant (round 1 for sites, when encountering the matching field for dropdowns, when the ATS is detected for playbooks).
- **Edit/append** when you learn something new that a future run would benefit from:
  - A new dropdown label variant you just matched manually
  - A form quirk you just hit and solved
  - A site's canonical answer to a repeated question
- **Do NOT** write runtime state here (current job progress, credentials, session cookies). This folder is source code — it gets committed. Runtime state lives in `~/Documents/jobs/tailored/state/` as before.
- **Do NOT** duplicate what's already in the HEADER. Knowledge files are for things that are too specific or too numerous to inline in every agent prompt.
