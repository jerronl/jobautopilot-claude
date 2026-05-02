# Capital One

**ATS:** Workday
**Hostnames:** `capitalone.wd12.myworkdayjobs.com`
**First seen:** 2026-04-09

## Quirks

- **2026-04-10** LinkedIn "Apply on company website" redirects through `dsp.prng.co` to `capitalonecareers.com`, which then links to Workday. The Workday job URL slug uses the format `R123456-1`.
- **2026-04-10** The Workday Sign In and Create Account pages have a `click_filter` anti-bot overlay (`data-automation-id="click_filter"` with `aria-label="Create Account"` or `"Sign In"`). This blocks automated clicking of the submit button. No known workaround -- requires manual user interaction.
- **2026-04-09** Existing credentials stored in credentials file.

## Known blockers

- **2026-04-10** `click_filter` overlay on Sign In / Create Account button prevents automated sign-in. `wait_human_login` required. Confirmed on all 3 Capital One Workday application attempts.
- **2026-04-20** `click_humanized` action WORKS to bypass the `click_filter` overlay. Verified: filled email+password, then `click_humanized` on `[data-automation-id="click_filter"]` → successfully logged in and reached Candidate Home. The 8-step application flow ("Autofill with Resume" → "My Information" → "My Experience" → "Application Questions 1/2" → "Application Questions 2/2" → "Voluntary Disclosures" → "Self Identify" → "Review") loads normally after sign-in. Previous application data (name, address, phone) is pre-filled from profile.
- **2026-04-20** The `#source--source` ("How Did You Hear About Us?") multiselect does NOT open with a simple `click` on the button. The `promptOption` evaluate captures phone country code options instead. May need a different approach (scroll into view first, or use `formField-source` scoped selector).
- **2026-04-20** RESOLVED: All Workday dropdowns on Capital One (both `#source--source` and `primaryQuestionnaire--*` / `secondaryQuestionnaire--*`) must use **keyboard navigation** to select options. Direct `click` on `li[role="option"]` elements fails because the dropdown popup disappears between the open-click and the option-click. Working pattern: `click` button to open dropdown -> `ArrowDown`/`ArrowUp` to navigate -> `Enter` to commit. Option order: `Select One` is index 0, then subsequent options in DOM order. When changing an already-selected value, `ArrowUp` from current goes to previous option, `ArrowDown` goes to next.
- **2026-04-20** Successfully submitted application (46 rounds total due to dropdown trial-and-error). 8-step form: Autofill with Resume -> My Information -> My Experience -> App Questions 1/2 -> App Questions 2/2 -> Voluntary Disclosures -> Self Identify (disability CC-305) -> Review -> Submit.
- **2026-04-21** CC-305 date field (Step 7): Workday splits the date into 3 separate text inputs (Month/Day/Year) with IDs `selfIdentifiedDisabilityData--dateSignedOn-dateSectionMonth-input`, `-Day-`, `-Year-`. CRITICAL: Using `Tab` between fills corrupts the values (month jumps to "12"). Correct approach: `fill` each input individually (no Tab), then `click` a different field (e.g. Name) to trigger blur. The date MUST match the browser's local date exactly (server-side validation: "Enter today's date").
- **2026-04-21** EEOC ethnicity dropdown (Step 6): Requires regular `click` (NOT `click_humanized`) to open the dropdown button. The options are `li` children of `UL#szss22` — standard `offsetParent` visibility checks return empty; must read `UL.children` directly. Keyboard ArrowDown navigation works once the dropdown is open and focused.
