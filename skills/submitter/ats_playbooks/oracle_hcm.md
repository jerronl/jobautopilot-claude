# Oracle HCM (Fusion / Redwood) ATS playbook

Applies to any URL matching `*.oraclecloud.com/hcmUI/CandidateExperience/*` or containing `/hcmUI/`.

Verified against `hdpc.fa.us2.oraclecloud.com` (Goldman Sachs Applied AI Researcher VP, 2026-04-07) — end-to-end submitted successfully after 21 rounds.

## Critical: `.cx-select-pill-section` pill components

Oracle HCM Redwood uses custom "pill" components for consent checkboxes, ethnicity, citizenship status, gender, etc. These respond ONLY to the real pointer chain — synthetic `el.click()` from inside `evaluate` is silently ignored.

### 🚫 What NEVER works

```json
{"type":"evaluate","expression":"document.querySelector('.cx-select-pill-section').click()"}
```
```json
{"type":"evaluate","expression":"(() => { const p = Array.from(document.querySelectorAll('.cx-select-pill-section')).find(e => e.textContent.includes('I consent')); p.click(); })()"}
```

Pills appear to highlight briefly then reset. `aria-pressed` never flips to `true`. Goldman Sachs burned 47 rounds on this exact pattern before the fix.

### ✅ What works

Use Playwright's native `click` action with a text-scoped selector:

```json
{"type":"click","selector":".cx-select-pill-section:has-text('I consent')"}
{"type":"wait","ms":500}
```

Verification — check `aria-pressed` or the `--selected` class modifier on the pill you just clicked:

```js
(() => {
    const pills = Array.from(document.querySelectorAll('.cx-select-pill-section')).filter(p => p.offsetParent);
    return pills.map(p => ({
        text: p.textContent.trim().slice(0, 40),
        pressed: p.getAttribute('aria-pressed'),
        selected: /--selected/.test(p.className),
    }));
})()
```

The clicked pill should show `aria-pressed: "true"` and classes containing `cx-select-pill-section--selected`. If it doesn't, the click didn't take — do NOT proceed; try a different selector or report blocked.

## Multi-section flow

Oracle HCM applications are split into numbered sections (`/apply/section/1`, `/section/2`, `/section/4`, etc.) and a final `/my-profile` review page. Unlike Workday, Oracle HCM **does** change the URL between sections, so URL-based progress tracking works here.

After committing pills in one section, click the section's continue/next button (typically labeled "Continue" or "Next" or the section number). The URL will advance to the next section.

## Other Oracle HCM quirks

- Input labels sometimes have `aria-labelledby` pointing to an element that's not immediately visible — prefer filling by `name` attribute or visible placeholder text when possible.
- Auto-complete searchable fields behave like Workday's Type C dropdowns: fill → wait 500ms → click the rendered `[role=option]`.
