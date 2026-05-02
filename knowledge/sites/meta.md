# Meta

**ATS:** Custom (metacareers.com)
**Hostnames:** `www.metacareers.com`
**First seen:** 2026-04-21

## Quirks

- **2026-04-21** Apply button is `div[role='button']:has-text('Apply now')` — NOT `a:has-text` or `button:has-text`. The page uses React DIV buttons throughout.
- **2026-04-21** EEOC radio buttons have no IDs and no name attributes. Use `input[type='radio'][value='<value>']` to click. Values observed: gender=(male/female/refuse), race=(native_american/asian/black/hispanic/native_hawaiian/white/multiple/refuse), veteran=(yes/yes_unprotected/no/decline), disability=(yes/no/decline).
- **2026-04-21** `label:has-text()` selectors time out — labels are not interactable via Playwright's label selector. Click the radio input directly with `input[type='radio'][value='...']`.
- **2026-04-21** Submit button is `div[role='button']:has-text('Submit')` — clicking it opens a confirmation dialog. The dialog has a `div[role='button']:has-text('Submit anyway')` button that must also be clicked to complete submission.
- **2026-04-21** Password / "Use a one-time code" section appears at bottom of application form for creating a Career Profile account — this is OPTIONAL. You do NOT need to fill these fields. Clicking "Submit anyway" skips account creation and submits the application.
- **2026-04-21** Location is a checkbox group — click `label:has-text('New York, NY')` to check the NYC location option. This label click works (unlike the EEOC radio labels).
- **2026-04-21** Resume upload field is `input[type='file']` followed by a 10s wait for parsing. Parser auto-fills name, email, phone, LinkedIn URL correctly from resume header.

## Submission confirmation

- Success URL pattern: `/resume/response/?success=1&req=...`
- Page title on success: `Application Received | Meta Careers`
