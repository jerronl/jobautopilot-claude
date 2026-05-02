# Intuit

**ATS:** Avature
**Hostnames:** `intuit.avature.net`
**First seen:** 2026-04-20

## Quirks

- **2026-04-20** Avature Select2 dropdowns (Gender, Race on EEO page) are AJAX-loaded. Typing a search term shows "Searching..." — need 2000ms+ wait after typing before options appear.
- **2026-04-20** Password field on account creation rejects `fill` action (value appears in DOM but has length 0 server-side). Must use `type` action instead for character-by-character input.
- **2026-04-20** "Continue" button on resume upload step has id `uploadFileResume`, not a generic "Continue" selector. `button:has-text('Continue')` times out.
- **2026-04-20** CSS selectors with numeric IDs (e.g. `#1366`) are invalid — use `[id='1366']` attribute selector format.
- **2026-04-20** Select2 clear button (`span.select2-selection__clear`, text "x") can be targeted with `[id='<fieldId>'] + .select2 .select2-selection__clear`.
- **2026-04-20** Select2 option elements have IDs like `li1165857` — clicking by `[id='li<value>']` is more reliable than `has-text()`.
- **2026-04-20** Multi-step form: Step 1 = Resume upload, Step 2 = Personal info (pre-filled from resume parse), Step 3 = EEO (Gender/Race Select2 + Veteran/Disability radios + Legal questions). Submit button on final page has id pattern `<formId>-save`.

## Canonical answers

- **Question:** "Are you legally authorized to work in the country in which you are applying to?"
  **Answer:** Yes (radio `[id='1385_7']`)

- **Question:** "Do you now or will you in the future need sponsorship for employment visa status?"
  **Answer:** No (radio `[id='1386_8']`)

- **Question:** "Have you previously been employed at Intuit?"
  **Answer:** No (radio `[id='1387_8']`)

- **Question:** "Are you 18 or older?"
  **Answer:** Yes (radio `[id='1389_7']`)

- **Question:** "Text message consent"
  **Answer:** Yes (radio `[id='1390_7']`)

## Submission confirmation

- Success URL pattern: `intuit.avature.net/en_US/externalCareers/Success`
- Confirmation phrase: `Thank you for applying`
