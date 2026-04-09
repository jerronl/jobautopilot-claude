# Point72

## ATS
Greenhouse (embedded via `job-boards.greenhouse.io/point72/jobs/<id>`)

## Hostnames
- `careers.point72.com` — marketing site with job detail pages (`/CSJobDetail?jobName=...&jobCode=...`)

## Quirks
- **Apply Now links**: The `a.o-button--primary` links on the CSJobDetail page point to `job-boards.greenhouse.io/point72/jobs/<greenhouse_id>`. These are NOT same-site links; they go to Greenhouse.
- **Stale listings**: The CSJobDetail page can still display a job listing even when Greenhouse has closed the position. Navigate to the Greenhouse link to confirm the job is still open.
- **Embed URL format**: `https://job-boards.greenhouse.io/embed/job_app?for=point72&token=<greenhouse_id>` redirects to `error=true` if the job is closed. The non-embed URL `https://job-boards.greenhouse.io/point72/jobs/<id>` also redirects to `careers.point72.com/` (homepage).
- **Greenhouse redirect**: Navigating directly to the `job-boards.greenhouse.io/point72/jobs/<id>` URL redirects back to `careers.point72.com/` homepage (not the application form). Use the embed format instead: `https://job-boards.greenhouse.io/embed/job_app?for=point72&token=<id>`.

## Confirmation
Unknown (both tested positions were expired).

## Verified
2026-04-09 — Two positions tested (Staff MLE GenAI PIT-0013047, MLE GenAI PIT-0013638), both expired on Greenhouse despite careers page still showing them.
