# Spotify

**ATS:** Custom (lifeatspotify.com — React/Next.js slide-out drawer form)
**Hostnames:** `www.lifeatspotify.com`
**First seen:** 2026-04-20

## Quirks

- **2026-04-20** Form lives in a slide-out drawer that opens when you click the "Apply nowApply" link on the job page. The link has `href="#"`.
- **2026-04-20** Drawer wrapper class: `jobformdrawer_wrapper__WrtXr`. When closed, adds `jobformdrawer_closed__DEbo3` and sets `pointerEvents: none` on wrapper + ancestors (`switchablecomponent_component__y4zgl`, `switchablecomponent_wrapper__c1HVX`).
- **2026-04-20** Form scrolls inside `.jobformdrawer_scrollable__cLtUq` (also `.drawer-scroller`). Must scroll this container to bring the Submit button into viewport before clicking. `scroller.scrollTop = scroller.scrollHeight` works.
- **2026-04-20** Submit button: `button[aria-label='Submit application']`. Clicking it **closes the drawer** — this IS the success behavior. No explicit confirmation page or confirmation text appears on the closed page.
- **2026-04-20** After successful submission, form fields reset to empty. Re-opening the drawer shows "Oops!... You did it again! It seems that you have already applied for this..." — Spotify's confirmation that the application was received.
- **2026-04-20** "Choose your location" button (`button.popover_button__nPfn2`) is for the Demographic survey section, NOT a required field. Applications submit without it.
- **2026-04-20** Pronoun checkboxes are optional. Input selectors: `input[name='pronouns'][value='he/him']` etc.
- **2026-04-20** After fresh navigation, the "Apply nowApply" link must be clicked to open the drawer. Clicking Submit without first opening the drawer properly will time out because ancestors have `pointerEvents: none`.
- **2026-04-20** Form method is `get` (React handles submission via JS, not standard form POST).
- **2026-04-20** CRITICAL TIMING: Submit click MUST be in a SEPARATE round from the fill round. Combining fill + scroll + submit in one round causes a race condition where the drawer closes without actually submitting (fields remain non-empty, no "Oops" message). The reliable pattern: Round N = fill all fields; Round N+1 = scroll + click Submit. After 8 seconds, verify: `hasClosed: true` AND `fieldsEmpty: true` AND `oopsMatch` present.

## Form fields

Required: `fullName`, `email`, `phone`, `currentCompany`, `currentLocation` (all `input[name='...']`)
Optional: `LinkedIn`, `GitHub`, `Portfolio`, `Other` (text inputs), `pronouns` (checkboxes), `additionalInformation` (textarea — good for cover letter), `marketing_consent` (checkbox)

## Submission confirmation

- Success URL pattern: same URL with `#` appended
- Confirmation phrase: "Oops!... You did it again! It seems that you have already applied for this" (only visible if you reopen the drawer after submitting)
- Primary signal: form fields reset to empty + drawer closes after Submit click

## 2026-04-21 — Alternate form layout (no drawer)

Some Spotify job pages show the application form **embedded directly in the page** (not in a slide-out drawer). In this layout:
- Form is visible on the page without any click needed
- File input selector: `input.react-aria-Input`
- Form fields use same `name` attributes (fullName, email, phone, etc.)
- `marketing_consent` checkbox is hidden — clicking `[name='marketing_consent']` times out; skip it
- Submit button: `button[type='submit']:has-text('Submit application')` (no aria-label needed)
- Success: `[class*="applycomplete_container"]` appears with "We'll take it from here / Thanks for applying" — URL stays the same
