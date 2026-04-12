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
