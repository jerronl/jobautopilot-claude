# JPMorgan Chase

**ATS:** Oracle HCM
**Hostnames:** `jpmc.fa.oraclecloud.com`
**First seen:** 2026-04-09

## Quirks

- **2026-04-10** PIN inputs are actually `#pin-code-1` through `#pin-code-6` (1-indexed, not 0-indexed). Each takes a single digit.
- **2026-04-10** Email entry (`#primary-email-0`): MUST use `type` action (character by character), not `fill`. The Oracle HCM Knockout.js binding does not detect Playwright's `fill` (which sets `value` directly). The `fill` action results in the NEXT button silently doing nothing.
- **2026-04-09** T&C checkbox is hidden; clicking its label (`label.legal-disclaimer-container`) opens a Terms popup. Click the "AGREE" button inside the popup to auto-check the checkbox.
- **2026-04-09** Section 1 (Personal Info) requires full mailing address including street address (`addressLine1`), postal code (`postalCode`), city, county, state. Profile import fills city/county/state but NOT street or zip. Ensure candidate has street address available.
- **2026-04-09** Section 4 (More About You / EEOC) has combobox dropdowns for Gender, Veteran Status, Military Status, Military Spouse. Use `type` action to enter search text, then click the `[role=option]` that appears. Direct `fill` does not work.
- **2026-04-09** Disability and Ethnicity are radio/checkbox inputs with hidden actual inputs. Click `<label for="...">` elements instead of the input directly.
- **2026-04-09** `fetch_email_code` search query should use `from:jpmorgan newer_than:15m` (the sender is JPMorgan, not oraclecloud).
- **2026-04-09** Submit validation shows "N issues that need to be fixed" banner and navigates back to section 1 with a "Go to Next Issue" button.

## Known blockers

- **2026-04-09** Requires street address (`addressLine1`) which is not in resume header (resume only shows "NY 11040"). Application cannot complete without it. Add `USER_ADDRESS_LINE1` env var.
