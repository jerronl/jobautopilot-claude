# IMC Trading

## ATS

Greenhouse EU: `job-boards.eu.greenhouse.io/imc/jobs/<id>`

Different from the US Greenhouse endpoint (`job-boards.greenhouse.io`). Both use the same react-select component library and `.select__option` class patterns.

## Security code verification

After clicking Submit, Greenhouse EU for IMC sends an 8-character alphanumeric security code to the applicant's email. The page renders 8 individual text inputs (`security-input-0` through `security-input-7`) and Submit is disabled until all 8 are filled.

**`fetch_email_code` is unreliable for this code.** The scanner misidentifies numeric substrings in the email footer (e.g. "NY 10011, USA" → returns "10011") as the code. The actual code is 8 characters, e.g. "ydksL0X0".

**Correct approach:**
1. Use `fetch_email_code` with `search_query: "subject:(security code) newer_than:30m"` — check `result.link` (not `result.code`) or check the full `result.text`
2. If result.code is clearly wrong (wrong length, all digits, looks like a zip), navigate to Gmail directly:
   - `navigate` to `https://mail.google.com/mail/u/0/#search/subject%3A(security+code)+newer_than%3A1d`
   - `click` the email row with `tr[jsmodel]:has-text('Security code for your application to IMC')`
   - `evaluate` to read the body: `document.querySelector('.a3s, .ii.gt').innerText.substring(0, 500)`
   - Body contains: "Copy and paste this code into the security code field on your application: <CODE>"
3. Fill each character into `[id='security-input-0']` through `[id='security-input-7']`

**CRITICAL: Form resets when navigating away.** If you navigate to Gmail to get the code, the Greenhouse EU form session is lost — ALL fields reset to blank. You must do a COMPLETE re-fill of the entire form in one round after returning from Gmail.

## Form fields

- `#first_name`, `#last_name`, `#email` — standard text inputs
- `#country` — react-select, phone dialing code selector. Options include "United States +1". Use `.select__option:has-text('United States +1')`.
- `#phone` — digits only, no formatting
- `#candidate-location` — react-select autocomplete using Google Places. Must use `type` (not `fill`) then wait 2000ms for autocomplete, then click `[role='option']:has-text('New York, NY, USA')`. The input value appears blank after selection — that's normal, the hidden value is committed.
- `#resume` — standard file input
- `#company-name-0`, `#title-0` — work history text inputs (most recent position)
- `#start-date-month-0` — react-select, use `.select__option:has-text('January')` etc.
- `#start-date-year-0` — text input (not dropdown)
- `[id='current-role-0_1']` — radio button for "I currently work here"
- `[id='school--0']` — react-select autocomplete for university name. Use `type` + wait 1500ms + click `.select__option:has-text('<exact school name>')`. `fill` does not trigger the search.
- `#question_7684747101` — "How did you hear about this role?" dropdown (Job board / Career website / etc.)
- `#question_7684748101` — sponsorship question (Yes/No)
- `#question_7684749101` — second immigration/authorization question (Yes/No)
- `#question_7684750101` — privacy policy agreement (I Agree)
- `#question_7684751101` — confidentiality agreement (I Agree)
- `[id='4005628101']` — EEOC Gender. Use `[role='option'] >> text='Male'` for exact match. **Do NOT use `.select__option:has-text('Male')` — it matches "Female" via substring.**
- `[id='4005629101']` — EEOC Race. Use `.select__option:has-text('Asian')`.

## Complete re-fill pattern

Because the form resets on navigation, keep all fill actions in a single round to avoid mid-fill navigation. Order: personal info → phone country code → phone → location → resume upload → work history → education → screening questions → EEOC → submit.

## Confirmation

URL changes to `https://job-boards.eu.greenhouse.io/imc/jobs/<id>/confirmation?...`
Text: "Step one, done! | Thanks for applying to join our team at IMC. We'll be in touch shortly with next steps."
`page.confirmed = true` is NOT set but URL suffix `/confirmation` and title "Thank you for applying" confirm success.
