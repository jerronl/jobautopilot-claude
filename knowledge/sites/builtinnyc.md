# BuiltIn / BuiltInNYC

**ATS:** Custom (Alpine.js + Knockout.js hybrid)
**Hostnames:** `www.builtinnyc.com`, `www.builtin.com`
**First seen:** 2026-04-10

## Quirks

- **2026-04-10** User is already logged in if `#logout` element exists. Form fields are pre-populated from the BuiltIn profile.
- **2026-04-10** Location field (`#locationDropdownInput`) uses Alpine.js with `x-on:input.debounce="searchLocations()"`. Plain `fill` does NOT trigger the search. Must use `type` action (character by character) then wait 2s, then `ArrowDown` + `Enter` to select from suggestions.
- **2026-04-10** School, Discipline, Degree fields also use Alpine.js autocomplete. `type` the text, wait 2-3s for suggestions to appear as `<div>` inside `<label class="list-group-item list-group-item-action text-truncate">`. Click the matching `label.list-group-item:has-text('...')` to commit the selection. Do NOT use ArrowDown+Enter — it clears the value.
- **2026-04-10** Education section requires clicking "ADD" button first to reveal School/Discipline/Degree/Date fields.
- **2026-04-10** Resume is selected via radio buttons (`input[name=resume]`). Previously uploaded resumes are available. The radio buttons are `visible: false` — use `evaluate` to set `checked=true` with `dispatchEvent(new Event('change',{bubbles:true}))`.
- **2026-04-10** Country dropdown (`#question_*`) uses numeric option values (e.g. `12775532006` for "United States of America"). Use `select` with `value` not `label`.
- **2026-04-10** Date selects for education use month names as labels ("January"..."December") and numeric values ("1"..."12"). Years go back to 1964.
- **2026-04-10** After clicking "Submit Application", a security code verification modal appears. The code is emailed to the user's email. The `#verification_code` input becomes visible along with an "Enter" button.
- **2026-04-10** `fetch_email_code` with `search_query: "subject:(code OR verification OR verify OR security) newer_than:30m"` should work to retrieve the code.
- **2026-04-10** Discipline autocomplete: "Computational Finance" is not a listed discipline. "Finance" is available and is the closest match.
- **2026-04-10** Degree autocomplete: "Master of Science" not listed. Options include "Master of Business Administration (M.B.A.)" and "Master's Degree".

- **2026-05-07** BuiltIn Easy Apply proxy submission sometimes fails with a "We Hit a Small Snag — We couldn't submit your application — please submit it on the company's site." error modal. This is not a blocking error — the modal contains a direct Greenhouse link (`https://job-boards.greenhouse.io/<company>/jobs/<id>`). Navigate to that URL and submit directly via Greenhouse. Detected for Affirm Manager ML Fraud (job 7710178003).
- **2026-05-07** Cookie banner buttons (Accept/Reject) are `type='submit'` — this causes `button[type='submit']:has-text('Submit Application')` to timeout because Playwright finds Accept/Reject first. Use more specific selector `.btn.btn-primary:has-text('Submit Application')` or ensure the cookie banner is dismissed first.
- **2026-05-07** Location field Alpine.js `x-on:input.debounce` does NOT fire when the field value is empty after a JS `value=''` clear followed by `fill`. The debounce only fires when actual keystrokes type characters. Use `press` key-by-key (each letter with 200ms wait) then ArrowDown+Enter — this is the only reliable approach.

## Known blockers

- **2026-04-10** Security code verification requires Gmail access. If Gmail is not signed in to the submit browser, cannot auto-fetch the code.
