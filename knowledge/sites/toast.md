# Toast

**ATS:** Clinch Talent (custom, hosted at careers.toasttab.com)
**Hostnames:** `careers.toasttab.com`
**First seen:** 2026-05-07

## Quirks

- **2026-05-07** Toast uses Clinch Talent ATS, NOT Greenhouse. The form is embedded inline on the job page (not a separate careers.greenhouse.io URL).
- **2026-05-07** Cookie consent modal (`[id='consent_agree']`) blocks the Submit button on first visit. Must click it before submitting. After first acceptance it does not reappear.
- **2026-05-07** Submit button (`button[name='next_step']`) is often off-screen. Must use `btn.scrollIntoView({behavior:'instant', block:'center'})` before clicking.
- **2026-05-07** Session persistence: first name, last name, email, phone, and EEOC checkboxes are remembered. Location city (`[id='question_2_0_4_4_0']`), postal code (`[id='question_2_0_4_0_7']`), and all `<select>` dropdowns (work auth, sponsor, consent, gender, disability, veteran) are NOT persisted on navigation — must be re-filled every attempt.
- **2026-05-07** File upload (`[id='question_2_0_4_0_1']`) is NOT preserved on navigation — must be re-uploaded every attempt.
- **2026-05-07** Verification code flow: after all required fields are valid (including file upload), clicking Submit shows a code entry modal on the same page. A 5-character alphanumeric code (e.g. AXV15, HTM44) is sent to the email address on file from `user-...@toast.mail.clinchtalent.com` with subject "Please verify your login at Toast Careers".
- **2026-05-07** Each new form submission generates a new code, invalidating all previous codes. Clicking Verify with a wrong code ALSO generates a new code.
- **2026-05-07** Code modal disappears if you navigate away from the page. Only enter the code in the SAME round as the form submission — use `fetch_email_code` with search_query `subject:"Toast Careers" newer_than:30m` AFTER clicking Submit, while still on the Toast page.
- **2026-05-07** `fetch_email_code` requires `subject:"Toast Careers" newer_than:30m` search query to find the right email. Broader queries (e.g. `subject:(verify)`) pick up other verification emails. The default `newer_than:10m` is also acceptable.
- **2026-05-07** Asian race: checkbox ID `[id='question_2_0_4_3_0_option_a157fc74eff301ea22fd139d831a3f13']` is so long it causes selector timeout. Use `evaluate` to find label with `innerText === 'Asian'` and click the adjacent checkbox.
- **2026-05-07** Confirmation: after successful Verify, the page returns to the job listing (no dedicated confirmation page). Signals of success: `hasCodeInput: false` (code modal gone) + `errors: []` (no error text). The page still shows "Apply now" but the application IS recorded.

## Canonical field IDs (2026-05-07)

- Location city: `[id='question_2_0_4_4_0']`
- Postal code: `[id='question_2_0_4_0_7']`
- Legally authorized to work (Yes/No select): `[id='question_2_0_4_0_4']`
- Require sponsorship (Yes/No select): `[id='question_2_0_4_0_5']`
- CCPA consent (I agree select): `[id='question_2_0_4_0_6']`
- Gender select: `[id='question_2_0_4_3_1']`
- Disability select: `[id='question_2_0_4_3_2']`
- Veteran status select: `[id='question_2_0_4_3_3']`
- Resume upload: `[id='question_2_0_4_0_1']`
- Verification code input: `[name='code']`
- Submit/Verify button: `button[name='next_step']`

## Canonical answers

- **Work authorization:** "Yes" (label) in `[id='question_2_0_4_0_4']`
- **Sponsorship required:** "No" (label) in `[id='question_2_0_4_0_5']`
- **CCPA consent:** "I agree" (label) in `[id='question_2_0_4_0_6']`
- **Gender:** "Man" (label) in `[id='question_2_0_4_3_1']`
- **Disability:** "No, I don't have a disability" (label) in `[id='question_2_0_4_3_2']`
- **Veteran status:** "I am not a protected Veteran" (label) in `[id='question_2_0_4_3_3']`

## Submission confirmation

- No dedicated confirmation URL — page stays on the job listing URL
- Success signal: code modal disappears (`hasCodeInput: false`) AND no error elements visible
- The "Apply now" button remains visible even after successful submission (expected)
