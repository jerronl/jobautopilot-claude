# BlackRock

## Hostnames
- `blackrock.wd1.myworkdayjobs.com` (Workday)
- `careers.blackrock.com` (redirects to Workday via external careers landing page)

## ATS
Workday (wd1). See `skills/ats_playbooks/workday.md` for generic Workday recipes.

## Application flow quirks

### Career site redirect
The URL from `careers.blackrock.com/job/-/-/45831/<id>` opens a landing page with a "Start Application" button. Clicking it navigates to `blackrock.wd1.myworkdayjobs.com/.../apply/autofillWithResume`.

### Resume parser (Step 1 -> 2)
- Auto-fills name, address, email, phone from resume
- Auto-fills work experience and education
- **Parser often creates duplicate or incorrect date entries for work history** — verify all dates against resume. Month/year spinbuttons sometimes get garbage values from parser errors.

### Phone Device Type dropdown (Step 2)
- The phone type dropdown options use `[role='option']` NOT `[data-automation-id='promptOption']`
- `[data-automation-id='promptOption']` is shared across other fields (source picker, phone country code) and will match wrong items

### How Did You Hear About Us (Step 2)
- Hierarchical multiselect with drill-down
- Top-level categories include "Career Sites"
- Under "Career Sites": "BlackRock Career Site"

### Application Questions (Step 4)
- "I affirm I will be able to provide documentation..." (work auth) — Yes/No dropdown
- "Will you need to obtain, renew, extend or transfer a visa..." — Yes/No dropdown
- **Cascading field:** Selecting "No" for the personal relationship question reveals a required textarea (id ends in `...c6ba3a9e0002`). Fill with "N/A" or a brief explanation.
- "Do you have a personal relationship with a BlackRock employee?" — Yes/No dropdown

### Voluntary Disclosures (Step 5)
- Gender, Race/Ethnicity, Hispanic/Latino, Veteran Status — all Type B dropdowns
- Race options include country suffix: "Asian (United States of America)"
- Veteran options: "I am not a veteran" (not just "No")
- Terms & Conditions checkbox: `#termsAndConditions--acceptTermsAndAgreements`

### Self Identify / Disability (Step 6)
- CC-305 form with Name, Date, disability status
- **Date field is a Workday spinbutton that rejects `fill`** — must use Calendar widget. See workday.md.
- Disability is a radio group using checkboxes with long hex IDs

### Submit (Step 7)
- Review page shows all entered data
- Submit button: `button:has-text('Submit')` (standard Workday submit)
- After submit, redirects to job search page with `Job_Application_ID` param
- A "Create Account" modal may overlay the page — can be ignored

### Work Experience date inputs (Step 3)
- Month/year spinbuttons: `fill` often creates "Invalid Date" — use `click` + `Ctrl+A` + `type` + `Tab` pattern
- IDs follow pattern: `#workExperience-N--startDate-dateSectionMonth-input`, `#workExperience-N--startDate-dateSectionYear-input`

### Gender dropdown — `:has-text('Male')` matches "Female"
- Workday Playwright `:has-text('Male')` substring-matches "Female". Use `:has-text('Male'):not(:has-text('Female'))` to select "Male" specifically.

### CC-305 date picker
- Click `[aria-label='Calendar']` to open, then `button[aria-label*='Selected Today']` to pick today.

### Degree labels
- "Post Graduate Degree" (not "Master's Degree")
- "Undergraduate Degree" (not "Bachelor's Degree")
