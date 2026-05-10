# Jane Street

**ATS:** Custom (janestreet.com own application form)
**Hostnames:** `www.janestreet.com`
**First seen:** 2026-05-06

## Quirks

- **2026-05-06** Apply form at `/join-jane-street/apply/<position_id>/` requires PDF resume — DOCX uploads are rejected with "Please enter a value with a valid extension."
- **2026-05-06** "How did you hear about us?" uses a custom `div.standard-dropdown.application-source` widget. The dropdown has many categories with hidden `li` elements. Opening the dropdown via `previewBox.click()` shows only the current visible section (e.g. "Jane Street games/puzzles"). To select a hidden option like "LinkedIn", use JS: `li.style.display = 'block'; li.style.visibility = 'visible'; li.click()`. This commits the value to `input[name="source"]` and updates the preview text.
- **2026-05-06** `interviewed` and `student` radio buttons (`[id="interviewed-false"]`, `[id="student-false"]`) are hidden — cannot be clicked via Playwright. Use JS: `el.checked = true; el.dispatchEvent(new Event('change', {bubbles:true}))`. The checked state persists, but the form may show "student fields" div even after setting `student=No`.
- **2026-05-07** Submit button has `class="v4-button submit g-recaptcha"` — but reCAPTCHA is **silent v3**, NOT v2. The visible iframe is the invisible-token harness, not a challenge widget. Direct `click button[type='submit']` works without any human interaction. Earlier 2026-05-06 note that this is v2 was a misread (same misread happened on 2026-04-09 SWE submission, see tracker).
- **2026-05-07** `current_position` field expects the user's CURRENT employer, not historical ones. Pull from the resume's first/current employment row, NOT from cover letter narrative (which often lists past employers).

## Known blockers

(none — all fields automatable; Submit click goes through directly)

## Submission confirmation

- Form replaces with: "Thank you for your application. We will follow-up with an email shortly. When we receive an application, we consider it for all available positions worldwide..."
- URL stays on `/join-jane-street/apply/<position_id>/`
