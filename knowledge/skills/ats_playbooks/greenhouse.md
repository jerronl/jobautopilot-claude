# Greenhouse ATS playbook

Greenhouse job boards use `job-boards.greenhouse.io/<company>/jobs/<id>` URLs.

## react-select dropdowns

Greenhouse uses react-select for many dropdowns (country, gender, race, veteran status, sponsorship).

### Identification
- Parent has class containing `select__control` or `select__input`
- Input has `role="combobox"` with `aria-autocomplete="list"`
- Hidden `<select>` may exist with class `select2-hidden-accessible`

### Filling pattern (Type C — searchable autocomplete)

1. Click the react-select container or its input
2. Type a prefix to filter options
3. Wait 300-500ms for filtering
4. Use ArrowDown + Enter to select (more reliable than clicking `[role='option']`)

### CRITICAL: has-text substring matching bug

**Never use `:has-text('Male')` to select "Male"** — it will match "Female" because "Female" contains the substring "Male". Playwright's `:has-text()` is a substring matcher.

Safe patterns:
- Type the exact value first to filter the list down to one option, then ArrowDown+Enter
- Use `text="Male"` (exact match) instead of `:has-text('Male')` (substring)
- Or use `[role='option'] >> text="Male"` for exact text matching

This applies to any option whose text is a substring of another option (Yes/No is fine, Male/Female is dangerous).

### ArrowDown+Enter vs direct click

For single-option selection after typing a prefix:
```json
{"type": "type", "selector": "input[role='combobox']", "value": "Mal"},
{"type": "wait", "ms": 300},
{"type": "press", "key": "ArrowDown"},
{"type": "press", "key": "Enter"}
```
This is MORE RELIABLE than clicking `[role='option']:has-text('...')` which can time out.

### "No" option click timeout

`[role='option']:has-text('No')` often times out in Greenhouse react-selects. Two reliable alternatives:

1. **Class-based selector (preferred):** `.select__option:has-text('No')` — works even when the role-based selector times out. Verified 2026-05-07 on Affirm Greenhouse form for sponsorship and hispanic_ethnicity fields.
2. **Keyboard:** ArrowDown+Enter after clicking the field to open the dropdown.

The class-based selector `.select__option:has-text(...)` is the most reliable because it targets Greenhouse's react-select option class directly rather than relying on the ARIA role attribute which Playwright may fail to resolve if the dropdown is collapsing.

### Scroll before opening dropdowns

When a form is long (many fields), dropdowns near the top of the form may be OFF-SCREEN (top coordinate is negative) after the page has scrolled to fill lower fields. Clicking an off-screen input can open the dropdown behind/above the viewport, causing subsequent clicks on options to timeout.

**Always scroll the field label into view before clicking the dropdown:**
```json
{"type": "evaluate", "expression": "(() => { const label = Array.from(document.querySelectorAll('label')).find(l => l.innerText && l.innerText.toLowerCase().includes('sponsorship')); if (label) label.scrollIntoView({behavior: 'instant', block: 'center'}); })()"},
{"type": "wait", "ms": 500},
{"type": "click", "selector": "[id='question_30359661003']"},
{"type": "wait", "ms": 800},
{"type": "click", "selector": ".select__option:has-text('No')"}
```

Do NOT click the label itself (it toggles the dropdown via its `for` attribute). Use `evaluate` to scroll it into view, then click the input field directly.

### Gender identity vs EEOC gender — avoid Male/Female ambiguity

Many Greenhouse forms have two separate gender dropdowns:
- "How do you identify? (gender identity)" — e.g. id=`4028768003`
- "Gender" (EEOC) — e.g. id=`gender`

Both have "Male" and "Female" as options. If both dropdowns are open simultaneously, `.select__option:has-text('Male')` is ambiguous. Use keyboard navigation instead when the field has "Female" as default focused option:
```json
{"type": "click", "selector": "[id='4028768003']"},
{"type": "wait", "ms": 800},
{"type": "press", "key": "ArrowDown"},
{"type": "wait", "ms": 300},
{"type": "press", "key": "Enter"}
```
This moves from Female (first/focused) → Male (second) and selects it.

## GDPR/Privacy checkbox

- Some Greenhouse forms have a GDPR consent checkbox at the bottom
- Ensure it's clicked only ONCE (odd number of times = checked). If clicked across multiple rounds, verify `checked` state before submitting.
- Selector: `input[type='checkbox']` near privacy policy text

## Country field quirk

The `#country` react-select may show options like "United States +1" (with the phone dialing code appended). This is the correct country option — click it. The field value will appear empty in the DOM input, but the selection is committed internally by react-select. The presence of a "Clear selections" button adjacent to the field confirms a selection was made.

## Cascading EEOC fields

Selecting "No" for Hispanic/Latino reveals a new "Please identify your race" (`#race`) dropdown. Always re-probe after filling Hispanic/Latino.

### Race options on Affirm Greenhouse form (`job-boards.greenhouse.io/affirm`)

After selecting "No" for Hispanic/Latino, the `#race` dropdown shows:
- American Indian or Alaskan Native
- Asian (use this for Asian / East Asian)
- Black or African American
- White
- Native Hawaiian or Other Pacific Islander
- Two or More Races
- Decline To Self Identify

Note: The `[id='4028769003']` multiselect for "How do you identify? (race/ethnicity)" has "East Asian" as an option — this is separate from the cascading EEOC `#race` dropdown. Both may appear on the same form.

### Gender identity `[id='4028768003']` — ArrowDown order

Options in order: Female → Male → Non-binary → I prefer not to say → I prefer to self describe.
- For "Male": click field, ArrowDown once (to highlight first = Female), ArrowDown again (to Male), Enter. OR type "Mal" then ArrowDown+Enter.
- Do NOT just ArrowDown once — that selects Female, not Male.

## File uploads

- Resume: `input[type='file']` with label containing "Resume"
- Cover letter: separate `input[type='file']` with label containing "Cover Letter"
- Both accept `.docx` and `.pdf`

## Submit

- Submit button: `button[type='submit']`, `button:has-text('Submit Application')`, or `input[type='submit']`
- `page.confirmed = true` after successful submission

## Greenhouse EU (`job-boards.eu.greenhouse.io`)

Same react-select patterns as US Greenhouse. Key differences:

### Security code verification

After Submit, an 8-character **alphanumeric** security code (e.g. "ydksL0X0") is emailed. The page shows 8 individual inputs (`security-input-0` through `security-input-7`); Submit stays disabled until all 8 are filled.

`fetch_email_code` is UNRELIABLE here — the scanner can return a numeric zip code from the email footer ("10011" from "NY 10011, USA") instead of the real code. If `result.code` looks wrong (all digits, wrong length), navigate to Gmail directly and read the email body which says: "Copy and paste this code into the security code field on your application: <CODE>".

**CRITICAL:** Navigating away from the form resets all fields. Re-fill the entire form in a single round when you return.

### candidate-location field

Must use `type` (not `fill`) + 2000ms wait for Google Places autocomplete, then click the `[role='option']` suggestion. Input appears blank after selection — that's normal; the hidden value is committed.

### School autocomplete

`[id='school--0']` is a react-select autocomplete. Use `type` + wait 1500ms + click `.select__option:has-text(...)`. `fill` does not trigger the search.
