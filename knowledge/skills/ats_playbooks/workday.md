# Workday ATS playbook

Applies to any URL matching `*.myworkdayjobs.com` or `wd[0-9]+.myworkdayjobs.com`.

All recipes below were empirically verified against `blackrock.wd1.myworkdayjobs.com` on 2026-04-08 using Playwright and end-to-end submitted successfully.

## Critical: Workday is a single-page app

**URL stays identical (`/apply/autofillWithResume`) across ALL 7 steps.** Do NOT use URL change as a progress signal on Workday. Judge progress by `page.interactive` — when the field set changes (e.g. from `[select-files, Next]` to `[firstName, city, email, ...]`) you've advanced a step.

The circuit breaker's "URL unchanged for 10 rounds" rule is wrong on Workday — override it by tracking whether `page.interactive` has *changed*, not the URL.

The 7 steps are always:
1. Autofill with Resume
2. My Information
3. My Experience (includes Education)
4. Application Questions
5. Voluntary Disclosures
6. Self Identify (US only — gender/ethnicity/veteran + T&C)
7. Review → Submit

## Step 1: Autofill with Resume

The page has ONLY two controls:
- File upload: `input[type=file][data-automation-id="file-upload-input-ref"]`
- Next button: `[data-automation-id="pageFooterNextButton"]`

Do NOT try to fill any other field on step 1 — they don't exist yet. Verified sequence:

```json
{"type":"set_input_files","selector":"input[type=file][data-automation-id=\"file-upload-input-ref\"]","path":"<resume.docx>"}
{"type":"wait","ms":6000}
{"type":"click","selector":"[data-automation-id=\"pageFooterNextButton\"]"}
{"type":"wait","ms":5000}
```

After this, step 2 "My Information" appears with fields:
- `#name--legalNameSection_firstName` / `_lastName`
- `#address--addressLine1`, `#address--city`, `#address--countryRegion`, `#address--postalCode`
- `#emailAddress--emailAddress`
- `#phoneNumber--phoneType`, `#phoneNumber--countryPhoneCode`, `#phoneNumber--phoneNumber`
- `#source--source` (the How Did You Hear About Us multiselect — see below)

Note: most of these get auto-populated by the resume parser. Check `page.interactive` to see what's already filled before filling again.

## Hierarchical multiselect (`#source--source` "How Did You Hear About Us", and similar)

This widget is a **drill-down picker**: top level shows categories, clicking a category reveals its children, clicking a leaf commits a chip.

Verified working sequence:

```json
{"type":"click","selector":"[id='source--source']"}
{"type":"wait","ms":800}
{"type":"click","selector":"[data-automation-id='promptOption']:has-text('<category>')"}
{"type":"wait","ms":600}
{"type":"click","selector":"[data-automation-id='promptOption']:has-text('<leaf label>')"}
{"type":"wait","ms":1000}
{"type":"click","selector":"body","position":{"x":10,"y":10}}
```

Verification (scoped to the source widget):
```js
(() => document.querySelector('[data-automation-id="formField-source"] [data-automation-id="selectedItem"]')?.textContent?.trim())()
```
→ should return the leaf label (e.g. "BlackRock Career Site").

### Discovering the category/leaf labels

The labels are company-specific — don't guess. After step 1 (click the field), dump visible promptOptions:

```json
{"type":"evaluate","expression":"(() => Array.from(document.querySelectorAll('[data-automation-id=\"promptOption\"]')).filter(o=>o.offsetParent).map(o=>o.textContent.trim()))()"}
```

Pick the category that looks closest to "Career Site" / "Job Board" / "LinkedIn" / "Employee Referral", click it, then dump promptOptions again to see the children, then click a leaf.

### Gotchas

- **`[data-automation-id="promptOption"]` is NOT unique.** The phone-country-code dropdown uses the same automation id. Always scope with `:has-text('<exact label>')`, and verify via the `formField-source` scoped `selectedItem` check — not by counting global promptOptions.
- **`.fill("LinkedIn")` does NOT trigger filtering.** It sets the input value without dispatching React keystroke handlers. Use the drill-down click approach, not typed filtering.
- The widget shows "Expanded" in its text while the popup is open — that's a status hint, not an error.

## Generic Workday dropdowns (`#education-NNN--degree`, `#personalInfoUS--gender`, etc.)

These are simpler than multiselect — single-select button openers. Verified sequence:

```json
{"type":"click","selector":"[id='<field-id>']"}
{"type":"wait","ms":400}
{"type":"click","selector":"<option selector by text or id>"}
{"type":"wait","ms":500}
```

Option rendering varies — sometimes `<li>`, sometimes `[role=option]`, sometimes `[data-automation-id="promptOption"]`. Dump the visible options first if unsure.

## Next button

Always use `[data-automation-id="pageFooterNextButton"]`. After clicking, wait 5s and re-probe `page.interactive` — the field set will change if you've advanced a step. If the same fields persist, there's an unfilled required field or a validation error; dump error messages with:

```js
Array.from(document.querySelectorAll('[data-automation-id*="error"], [role="alert"]')).filter(e=>e.offsetParent).map(e=>e.textContent.trim())
```

## Submit button (step 7)

Final step has a Submit button instead of Next:

```json
{"type":"click","selector":"[data-automation-id=\"pageFooterSubmitButton\"]"}
{"type":"wait","ms":6000}
```

Verify submission by checking for confirmation phrases in `page.text` ("thank you", "application received", "we've received your application") or URL change to a `/thankYou` or `/Success` path.

## click_filter anti-bot overlay (some tenants)

Some Workday tenants (confirmed: `geico.wd1.myworkdayjobs.com`) place a `<div data-automation-id="click_filter" aria-label="Create Account" role="button">` overlay on top of the actual submit button (`data-automation-id="createAccountSubmitButton"` / `signInSubmitButton`). The actual button has `tabindex="-2"`.

This div is a reCAPTCHA/anti-bot gate:
- Clicking the overlay div directly may close the tab (bot detection triggered).
- Hiding the overlay (`display:none` / `pointer-events:none`) and clicking the underlying button succeeds as a click but the server silently rejects (no reCAPTCHA token).
- `form.submit()` via JS reloads the page without advancing.

**No known automated workaround.** Use `wait_human_login` to ask the user to click the button manually. If user doesn't act, mark as `blocked: workday_click_filter_recaptcha`.
