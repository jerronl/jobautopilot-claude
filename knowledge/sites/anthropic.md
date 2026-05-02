# Anthropic

**ATS:** Greenhouse (job-boards.greenhouse.io)
**Hostnames:** `job-boards.greenhouse.io/anthropic`
**First seen:** 2026-04-20

## Quirks

- **2026-04-20** Application URL pattern: `https://job-boards.greenhouse.io/anthropic/jobs/<id>`. Can append `?gh_src=LinkedIn` for source tracking.
- **2026-04-20** Greenhouse uses react-select flyout dropdowns for all select fields. The `button[aria-label="Toggle flyout"]` buttons are indexed 0-N on the page. Use `button[aria-label='Toggle flyout'] >> nth=N` to target specific ones.
- **2026-04-20** For EEOC fields (gender, hispanic_ethnicity, veteran_status, disability_status), clicking the `#<field_id>` input directly opens the flyout. No need to find the toggle button.
- **2026-04-20** Use `:text-is('No')` instead of `:has-text('No')` when selecting "No" options. `:has-text('No')` also matches longer options like "No, I do not have a disability" which causes strict-mode ambiguity or wrong selection.
- **2026-04-20** Country field is optional and uses phone-code format (e.g. "United States +1"). Can be skipped.
- **2026-04-20** reCAPTCHA v3 is present but invisible. Does NOT block submission.
- **2026-04-20** After successful submit, redirects to `/confirmation?gh_src=LinkedIn` with `page.confirmed=true` and text "Thank you for applying!"

## Canonical answers

- **"Are you open to working in-person in one of our offices 25%?"** → Yes
- **"AI Policy for Application"** → Yes (confirms agreement to AI partnership guidelines)
- **"Do you require visa sponsorship?"** → No (from USER_NEED_SPONSOR)
- **"Will you now or in the future require employment visa sponsorship?"** → No (from USER_NEED_SPONSOR)
- **"Are you open to relocation for this role?"** → Yes (candidate is in NYC, role lists NYC)
- **"Have you ever interviewed at Anthropic before?"** → No

## Known blockers

- None. Application submits successfully.

## Submission confirmation

- Success URL pattern: `/jobs/<id>/confirmation`
- Confirmation phrase: "Thank you for applying! Your application has been received."
