# GEICO

**ATS:** Workday
**Hostnames:** `geico.wd1.myworkdayjobs.com`
**First seen:** 2026-04-20

## Quirks

- **2026-04-20** LinkedIn "Apply on company website" redirects through `click.appcast.io` to `geico.wd1.myworkdayjobs.com`.
- **2026-04-20** Job page shows "Autofill with Resume", "Apply Manually", and "Use My Last Application" links.
- **2026-04-20** Cookie consent banner appears on first load.

## Known blockers

- **2026-04-20** `click_filter` overlay on Create Account button (`data-automation-id="click_filter"` with `aria-label="Create Account"`). Actual submit button has `tabindex="-2"`. No signInSubmitButton detected on the Create Account page. Confirmed `click_filter` matches the pattern documented in the Workday playbook.
- **2026-04-20** `click_humanized` action bypasses the click_filter: scroll into view + mouse warmup (2-3 random moves) + jitter click. Verified: tab stays open, isTrusted=true, account creation form appears. See Workday playbook.
