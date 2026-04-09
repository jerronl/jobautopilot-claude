# Two Sigma

**ATS:** Custom iCIMS-based portal
**Hostnames:** `careers.twosigma.com`
**First seen:** 2026-04-09

## Quirks

- **2026-04-09** All form element IDs start with digits (e.g. `5501-next`, `5506-save`). Must use attribute selectors `[id='5501-next']` instead of `#5501-next`.
- **2026-04-09** Multi-step SPA form: Upload Resume -> About You -> Role Specific Questions -> Confirm Application. URL stays `ApplicationForm?jobId=NNNNN` throughout all steps.
- **2026-04-09** Profile data pre-fills from previous applications (address, EEOC, work auth, education, work history). Always verify pre-filled values.
- **2026-04-09** Next button pattern: `[id='XXXX-next']` where XXXX changes per step. Submit button: `[id='XXXX-save']`.
- **2026-04-09** `page.interactive` includes the full site navigation (60+ nav links) — filter to form elements only.
- **2026-04-09** Radio buttons and checkboxes use `label[for='ID']` click pattern. IDs follow `XXXX-N_NNNN` format (e.g. `5502-6_6981`).

## Canonical answers

- **Question:** "How many years of experience as a software engineer, excluding internships/co-ops?"
  **Answer:** 10+
  **Reason:** matches candidate profile

## Submission confirmation

- Success URL pattern: `careers.twosigma.com/careers/Success?jobId=`
- Confirmation phrase: `Thank you for your interest, <name>! Your application for <role> has been submitted.`
