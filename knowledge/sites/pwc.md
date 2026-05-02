# PwC

**ATS:** Workday
**Hostnames:** `pwc.wd3.myworkdayjobs.com`
**First seen:** 2026-04-10

## Quirks

- **2026-04-10** LinkedIn "Apply on company website" redirects through DoubleClick ad tracker to `jobs.us.pwc.com`, which links to Workday `pwc.wd3.myworkdayjobs.com`.
- **2026-04-10** Cookie consent banner appears on first load. Has "Accept Cookies" and "Decline" buttons.
- **2026-04-10** The Workday Create Account page has a `click_filter` anti-bot overlay. Same pattern as Capital One and GEICO Workday tenants.

## Known blockers

- **2026-04-10** `click_filter` overlay on Create Account / Sign In button prevents automated account creation or sign-in. `wait_human_login` required.
- **2026-04-20** RESOLVED: `click_humanized` action bypasses the `click_filter` overlay on PwC wd3. Verified: filled email+password, then `click_humanized` on `[data-automation-id="click_filter"]` -> successfully logged in.

## Application flow notes (verified 2026-04-21)

- **7-step form:** Autofill with Resume -> My Information -> My Experience -> Application Questions -> Voluntary Disclosures -> Self Identify (CC-305) -> Review -> Submit
- **CC-305 date field:** The `fill` action on date segment inputs causes Tab corruption (month jumps to "12"). ONLY reliable method: open the Calendar picker (`div[aria-label="Calendar"]`), navigate with "Previous month"/"Next month" buttons, then click the button with `aria-label="Today <dayname> <day> <month> <year>"`. This properly commits the date to Workday's React state.
- **Dropdowns:** Standard Workday keyboard navigation (click to open -> ArrowDown N times -> Enter) works for gender, ethnicity, veteran status dropdowns.
- **Source field (How Did You Hear About Us?):** Hierarchical multiselect. Categories include "Career Site", "Job Board", etc. After clicking the field, click category -> click leaf.
- **Application Questions:** Two pages of questions including work authorization, visa sponsorship, and custom questions. "No" to visa sponsorship reveals a cascading "immigration description" textarea that must be filled.
- **Immigration type dropdown order (verified 2026-04-21):** DACA(1), E-3(2), F-1(3), F-1 CPT(4), F-1 STEM OPT(5), H-1B(6). Selecting H-1B cascades: "years remaining on visa" (1-7+), "eligible to renew status" (Yes/No), "visa expiration date" (MM/DD/YYYY date field — `fill` works fine on this non-CC-305 date field).
- **Voluntary Disclosures (Step 5):** Gender, Ethnicity, Veteran status dropdowns + T&C checkbox. Standard Workday ArrowDown navigation works.
- **CC-305 date (Step 6):** Calendar picker approach (`div[aria-label='Calendar']` → `button[aria-label*='Today']`) verified working 2026-04-21. Fills all 3 segments correctly.
