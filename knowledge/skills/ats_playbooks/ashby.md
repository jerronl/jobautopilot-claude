# Ashby ATS Playbook

**Domain pattern:** `jobs.ashbyhq.com`

## Form structure

- Single-page application form at `/<company>/<job-id>/application`
- System fields: `_systemfield_name` (legal name), `_systemfield_email`, `_systemfield_resume`
- Custom questions use UUID-based IDs (e.g. `1c58022a-0e86-4f84-b9a2-69d5e775baec`)
- Yes/No questions: rendered as `<button type="submit">Yes</button>` / `<button type="submit">No</button>` with a hidden `<input type="checkbox">` that tracks state
- When a Yes/No button is selected, it gets CSS class `_active_y2cw4_58`; the hidden checkbox becomes `checked: true`
- Cover letter field: `#cover_letter` (file input, optional)

## Selector gotchas

- **UUID IDs start with digits** — always use `[id='...']` attribute selector, never `#...`
- Multiple `button[type="submit"]` on the page (Upload file, Replace, Yes, No, Submit Application) — use `:has-text('Submit Application')` to target the submit button
- `document.querySelector('button[type="submit"]')` returns the first one (Upload file), not Submit

## Resume autofill

- Ashby has a "Autofill from resume" feature that parses uploaded resumes
- After uploading, some fields auto-populate; verify them against profile data

## Radio button groups (multi-option questions)

Some Ashby forms use custom radio buttons instead of Yes/No buttons. Structure:

```html
<div class="_option_1v5e2_35 false">
  <span class="_container_ruukg_29" data-disabled="false">
    <span class="_circle_ruukg_74"></span>
    <input type="radio" id="..." name="...">
  </span>
  <label for="..." class="_label_1v5e2_43">New York</label>
</div>
```

**Critical:** The React event handler is on `span._container_ruukg_29`, NOT on the input, label, or option div. Clicking the input directly checks it in the DOM but React state does not update — form validation will reject the submission.

**Working selector pattern:**
```json
{"type": "click", "selector": "span[class*='_container_ruukg'] >> nth=N"}
```

First probe to get the index mapping:
```json
{"type": "evaluate", "expression": "(() => { const containers = document.querySelectorAll('span[class*=\"_container_ruukg\"]'); return JSON.stringify([...containers].filter(c=>c.offsetParent).map((c,i)=>({ idx:i, label: c.parentElement?.querySelector('label')?.textContent?.trim() }))); })()"}
```

When selected, the parent `_option_` div's class changes from `_option_1v5e2_35 false` to `_option_1v5e2_35 true`.

Verified 2026-04-09 on Distyl AI Applied AI Researcher application (11 rounds to discover this pattern).

## Checkbox acknowledgments

Some Ashby forms have acknowledgment checkboxes (e.g. "I acknowledge that I have opened, read, and understood the Arbitration Agreement"). These use a different container class than radios:

- Container: `span._container_1hpbx_29` (NOT `_container_ruukg_29`)
- **Working approach:** Click the `<label>` element using `:has-text()`:
  ```json
  {"type": "click", "selector": "label:has-text('I acknowledge that I have opened')"}
  ```
- Verify with: check `input.checked === true` on the hidden checkbox

## Submission

- Submit button: `button:has-text('Submit Application')`
- Invisible reCAPTCHA v3 present (`g-recaptcha-response` textarea, hidden)
- reCAPTCHA token auto-fills on submit click; no manual CAPTCHA interaction needed
- On success, page shows "Success" heading followed by "Thank you for your interest in [Company]!"
- URL does not change after submission

## Spam detection

- Ashby may flag automated submissions as spam (seen 2026-04-08)
- A fresh browser session with clean cookies may bypass the spam flag
- If flagged, the form silently fails — no error message shown, page just stays on the form

## Confirmation detection

- The runner's `page.confirmed` may return `false` even on success
- Check `page.text` for "Success" or use evaluate to read body text for confirmation
- Confirmation phrase: "Thank you for your interest in"

## Phone field accepts digits-only

If the phone placeholder is `1-415-555-1234` style, Ashby validates as a phone number and rejects formatted input like `(347) 644-8088` with a `Missing entry for required field: Phone` error. Use digits-only `3476448088`. (Verified at Notion 2026-04-29.)

## Notion-specific quirks

- Pronouns are required as a radio group: click `label:has-text('He/Him')`, etc.
- Location field is a custom autocomplete — use `type` to enter a partial query, then `click ._result_v5ami_103:has-text('New York City, New York, United States')` to commit.
- Single Yes/No buttons need the fieldEntry-scoped selector pattern: `._fieldEntry_17tft_29:has-text('full label text') button:has-text('Yes')`.
- Yes/No buttons commit independently; verify with `evaluate` reading `class.includes('_active_y2cw4_58')` on the button.

## Confirmation phrase variants

- Notion / Rillet / OpenAI (2026-04-29): "Your application was successfully submitted. We'll contact you if there are next steps."
- Sierra (older): "Awesome! Your application was successfully submitted. We'll review your profile and contact you if we find a fit."

## Date picker fields (e.g. "When can you start?")

If a field has placeholder "Pick date..." and class `_input_vhnr2_29`, it's an Ashby date input. To fill:
1. Click the input
2. `type` value `MM/DD/YYYY` (e.g. `06/01/2026`)
3. Press `Enter` to commit

Confirmed at OpenAI Codex 2026-04-29.

Note: the `success: true` keyword check on body text can match other words ("successfully" appears in product copy too). Always look for the EXACT phrase "application was successfully submitted" or "Your application was" to confirm.
