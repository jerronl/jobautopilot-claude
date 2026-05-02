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

`[role='option']:has-text('No')` often times out in Greenhouse react-selects. Use ArrowDown+Enter after typing "No" instead.

## GDPR/Privacy checkbox

- Some Greenhouse forms have a GDPR consent checkbox at the bottom
- Ensure it's clicked only ONCE (odd number of times = checked). If clicked across multiple rounds, verify `checked` state before submitting.
- Selector: `input[type='checkbox']` near privacy policy text

## Country field quirk

The `#country` react-select may show options like "United States +1" (with the phone dialing code appended). This is the correct country option — click it. The field value will appear empty in the DOM input, but the selection is committed internally by react-select. The presence of a "Clear selections" button adjacent to the field confirms a selection was made.

## Cascading EEOC fields

Selecting "No" for Hispanic/Latino reveals a new "Please identify your race" (`#race`) dropdown. Always re-probe after filling Hispanic/Latino.

## File uploads

- Resume: `input[type='file']` with label containing "Resume"
- Cover letter: separate `input[type='file']` with label containing "Cover Letter"
- Both accept `.docx` and `.pdf`

## Submit

- Submit button: `button[type='submit']`, `button:has-text('Submit Application')`, or `input[type='submit']`
- `page.confirmed = true` after successful submission
