# Stripe

## ATS
Greenhouse (embedded via iframe `#grnhse_iframe` on `stripe.com/jobs/listing/...`)

## Hostnames
- `stripe.com` — job listing pages at `/jobs/listing/<role>/<greenhouse_id>`
- `job-boards.greenhouse.io` — actual application form (cross-origin iframe)

## Quirks
- **Cross-origin iframe**: The application form is inside `#grnhse_iframe`, which is cross-origin. The runner's `fill` and `evaluate` actions do NOT support the `iframe` parameter. Only `click` and `upload` do.
- **Solution**: Navigate directly to `https://job-boards.greenhouse.io/embed/job_app?for=stripe&token=<greenhouse_id>` to render the form as a standalone page. Extract the token from the Stripe job URL (last path segment).
- **React-select dropdowns**: Greenhouse uses react-select for Country, Location, Gender, Hispanic/Latino, Veteran, Disability. These are Type C (searchable autocomplete).
  - Pattern: click the dropdown container -> wait -> evaluate to capture option IDs -> click by exact `#react-select-<field>-option-<N>` ID.
  - DO NOT use `:has-text('...')` for option clicks -- the dropdown closes between the evaluate and click actions. Use exact option IDs instead.
- **Country of residence**: The dropdown ID pattern is `react-select-question_<id>-option-<N>`. Type "United" to filter, then click the US option by ID.
- **Location field**: This is also a react-select autocomplete. Type "New York" then click `[role='option']:has-text('New York, NY, USA')`.
- **Checkbox inputs for multi-select questions** (e.g. "Where in the US are you located?"): Use exact checkbox ID `[id='question_<qid>[]_<option_id>']`. DO NOT click labels with `:has-text('US')` -- "US" substring matches "Australia" and other country labels.
- **Phone**: Standard text input, accepts formatted phone like `(555) 123-4567`.
- **Resume upload**: `input[type='file']` with `data-source='paste'` attribute. Standard upload works.
- **Cover letter**: Textarea field, fill with text content.

## Confirmation
`page.confirmed=true` after submit. No specific confirmation URL -- stays on same page with confirmation message.

## Verified
2026-04-09 — Applied to Machine Learning Engineer, Payments ML Accelerator (token 7079044). 22 rounds.
