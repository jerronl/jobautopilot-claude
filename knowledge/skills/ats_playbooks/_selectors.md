# Cross-ATS selector and evaluate rules

These rules are not specific to any one ATS — they apply everywhere Playwright touches a page.

## CSS selector validity

**Never use an ID selector that starts with a digit or contains a dash-digit pattern that CSS treats as invalid.** Examples that THROW `SyntaxError: Failed to execute 'querySelectorAll'`:

- `#5abc`
- `#0-1-additional-questions-dropdown`
- `#0-1-foo`

Use attribute selectors instead — these always work:

- `[id='5abc']`
- `[id='0-1-additional-questions-dropdown']`
- `[id='0-1-foo']`

Verified 2026-04-08 with a standalone test: `page.locator("#0-1-foo").count()` throws, `page.locator("[id='0-1-foo']").count()` returns 1. This was the Millennium LinkedIn Easy Apply failure mode — the additional-questions dropdown IDs start with `0-1-`.

### Mandatory recovery on SyntaxError

If the runner returns `Locator.count: SyntaxError` or `Page.evaluate: SyntaxError: Failed to execute 'querySelectorAll'`, the next round MUST rewrite the offending selector to the `[id='...']` form. **Never resubmit the same failing selector** — that's how Millennium burned 30+ rounds.

## `evaluate` expression rules

Playwright's `page.evaluate` requires an **expression**, not a statement. Bare `const x = …; x` raises `SyntaxError: Unexpected token 'const'`.

Wrap multi-statement logic in an IIFE:

```js
(() => {
    const x = document.querySelector('…');
    return x ? x.textContent : null;
})()
```

## 🚫 NEVER click form controls from inside `evaluate`

`el.click()` in JS fires only a synthetic `click` event. Modern ATS components ignore synthetic clicks:

- Oracle HCM Redwood `.cx-select-pill-section` pills
- Workday JET buttons / radio groups
- Some MUI / React custom toggles
- Various React-based Next/Submit buttons that listen on `pointerdown` → `pointerup` → `click`

Always use a real `click` action with a selector:

```json
{"type": "click", "selector": ".cx-select-pill-section:has-text('I consent')"}
```

Not:

```json
{"type": "evaluate", "expression": "document.querySelector('.cx-select-pill-section').click()"}
```

**After clicking any custom toggle, verify it committed** before moving on. Use an `evaluate` that reads `aria-pressed`, `aria-selected`, `aria-checked`, or a `--selected` class on the element you just clicked.

## Scoped selectors when `data-automation-id` repeats

Some frameworks (Workday especially) reuse the same `data-automation-id` across multiple unrelated widgets on the same page. For example, `[data-automation-id="promptOption"]` appears in both the "How did you hear about us" multiselect AND the phone country code dropdown.

Always scope:

- By text: `[data-automation-id='promptOption']:has-text('Career Site')`
- By ancestor: `[data-automation-id='formField-source'] [data-automation-id='promptOption']`
- Verify by scoped descendant check, never by global count.
