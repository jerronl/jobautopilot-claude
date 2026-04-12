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
