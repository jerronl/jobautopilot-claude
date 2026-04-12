# Jump Trading

**ATS:** Greenhouse (embedded)
**Hostnames:** `www.jumptrading.com` (with embedded `job-boards.greenhouse.io` iframe)
**First seen:** 2026-04-10

## Quirks

- **2026-04-10** Jump Trading uses a custom career page at `jumptrading.com/hr/job?gh_jid=<id>` with an embedded Greenhouse iframe (`job-boards.greenhouse.io/embed/job_app`).
- **2026-04-10** All Greenhouse URLs (`boards.greenhouse.io/jumptrading/jobs/<id>` and `job-boards.greenhouse.io/jumptrading/jobs/<id>`) redirect back to `jumptrading.com/hr/job?gh_jid=<id>`.
- **2026-04-10** The Greenhouse embed iframe is cross-origin and cannot be accessed directly from the parent page.
- **2026-04-10** The `job_app` embed type only shows the job description and benefits -- the application form is NOT included in the embed. The `#apply-form` div on the parent page is empty.
- **2026-04-10** "Opt-Out Signal Honored" banner appears on page load (DNT/GPC signal detected).

## Known blockers

- **2026-04-10** No visible application form on the page. The Greenhouse embed shows only job description. Manual application may be needed through a different entry point, or the form may only load in non-headless browsers without DNT/GPC signals.
