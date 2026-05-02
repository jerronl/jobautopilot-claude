# Airbnb

**ATS:** Greenhouse (embedded)
**Hostnames:** `careers.airbnb.com`, `job-boards.greenhouse.io` (for=airbnb)
**First seen:** 2026-04-20

## Quirks

- **2026-04-20** Airbnb embeds Greenhouse in a cross-origin iframe `#grnhse_iframe`. The `fill` action does NOT support iframe parameter. Navigate directly to the embed URL instead: `https://job-boards.greenhouse.io/embed/job_app?for=airbnb&token=<job_id>` where `<job_id>` is the numeric ID from the careers URL (e.g. `7747259` from `careers.airbnb.com/positions/7747259/`).
- **2026-04-20** Navigating to `https://job-boards.greenhouse.io/airbnb/jobs/<job_id>` redirects back to `careers.airbnb.com`. Must use the `/embed/job_app` URL format.
- **2026-04-20** Country phone code dropdown is react-select Type C. Type "United" then click option containing "United States (+1)".
- **2026-04-20** Location dropdown is react-select Type C. Type first 3 chars of desired location.

## Canonical answers

- **Question:** "How did you hear about this job?" (react-select)
  **Answer:** Option index 1 = "Third-party website" (for jobs found via Tech:NYC or similar)
  **Reason:** Maps to job board discovery source

- **Question:** Gender (react-select)
  **Answer:** Option index 0 = "Male"

- **Question:** Race/Ethnicity (react-select)
  **Answer:** Option index 1 = "Asian (Not Hispanic or Latino)"

- **Question:** Veteran Status (react-select)
  **Answer:** Option index 1 = "I am not a protected veteran"

- **Question:** "Are you legally authorized to work in the United States?" (react-select)
  **Answer:** Option index 0 = "Yes"

- **Question:** "Will you now, or in the future, require sponsorship..." (react-select)
  **Answer:** Option index 2 = "No"

- **Question:** "Are you subject to any non-compete, non-solicitation, or other restrictive covenants?" (react-select)
  **Answer:** Option index 1 = "No"

- **Question:** "Have you previously worked at Airbnb?" (react-select)
  **Answer:** Option index 1 = "No"

## Known blockers

- None observed. reCAPTCHA v3 badge present but does not block submission.

## Submission confirmation

- Confirmation phrase: "Thank you for applying"
- `page.confirmed: true` after submit click
