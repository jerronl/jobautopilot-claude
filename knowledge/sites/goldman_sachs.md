# Goldman Sachs

**ATS:** Oracle HCM
**Hostnames:** `hdpc.fa.us2.oraclecloud.com`
**First seen:** 2026-04-20

## Quirks

- **2026-04-20** Career site is at `/hcmUI/CandidateExperience/en/sites/LateralHiring/`. Job URLs: `.../job/<id>/`.
- **2026-04-20** Apply URL: `.../job/<id>/apply/email?mode=job&iis=LinkedIn`. Email entry uses Knockout.js binding -- MUST use `type` action, not `fill`, for the email field (`#primary-email-0`).
- **2026-04-20** T&C checkbox: click label "I agree with the terms and conditions" to open popup, then click "Agree" button. Checkbox ID: `#legal-disclaimer-checkbox`.
- **2026-04-20** PIN verification uses 6 separate inputs `#pin-code-1` through `#pin-code-6` (1-indexed). After entering email + T&C + Next, a 6-digit code is sent to the email.
- **2026-04-20** If already authenticated (session cookie from prior application), clicking "Apply Now" from job details skips email/PIN and goes directly to `/section/1/`.
- **2026-04-20** `fetch_email_code` may return a stale code from a prior GS application if both occurred within the same Gmail search window. The site sends codes from the same sender, so `newer_than` alone doesn't distinguish them.
- **2026-04-20** 4-section application: section/1/ (personal info), section/2/ (experience), section/3/ (screening questions), section/4/ (submit).

## Canonical answers

- **Question:** "Have you ever worked for or applied to Goldman Sachs before?"
  **Answer:** No
  **Reason:** Unless work history shows GS employment.

- **Question:** "Are you Hispanic or Latino?"
  **Answer:** No (from USER_HISPANIC env var)

- **Question:** "What is your gender?"
  **Answer:** Male (from USER_GENDER env var)
  **Note:** Pills have leading whitespace (" Male", " Female"). Use temp ID assignment via evaluate, not `:text-is()`.

- **Question:** "What is your race?"
  **Answer:** Asian (from USER_RACE env var)
  **Note:** Cascading: selecting "No" for Hispanic reveals Race options.

- **Question:** "Are you legally authorized to work in the US?"
  **Answer:** Yes (from USER_WORK_AUTH env var)
  **Note:** Cascading: "Yes" reveals Citizenship Type dropdown. Select "U.S. Citizen or National".

- **Question:** "Require visa sponsorship now or in the future?"
  **Answer:** No (from USER_NEED_SPONSOR env var)
  **Note:** Cascading: a visa type combobox may appear. If required, type "N/A" and select.

## Known blockers

- **2026-04-20** Oracle HCM section/1/ can get stuck in infinite loading ("You're all set!" with `oj-progress-bar` spinner) after email authentication succeeds. The form never renders. Reloading shows "Something went wrong. Try again later." Signing out and re-entering via Apply Now produces the same stuck state. The application draft may be corrupted. No known workaround except waiting and retrying later.
- **2026-04-20 (retry)** hCaptcha is no longer present on GS Oracle HCM. Email + T&C + Next flow works. PIN verification page loads normally. However, `fetch_email_code` returns stale code (829820) from a prior GS application session. After entering the stale code, "The code isn't valid" error appears. "Send New Code" was rate-limited ("Try again later"). Need to wait longer between code requests, or use a narrower Gmail search query to find only the newest code.

## Submission confirmation

- Success URL pattern: `/section/4/` or confirmation page after final Submit
- Confirmation phrase: `page.confirmed = true` from runner
