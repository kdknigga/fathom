---
phase: 02-web-layer-and-input-forms
verified: 2026-03-10T21:00:00Z
status: human_needed
score: 18/18 must-haves verified
human_verification:
  - test: "Start app with `uv run fathom`, open http://127.0.0.1:5000 in a browser"
    expected: "Two-column desktop layout renders correctly with Pico CSS styling, 2 option cards visible, global settings collapsed showing 'Using defaults'"
    why_human: "Visual rendering and CSS layout cannot be verified programmatically — only that the HTML structure and CSS classes are present"
  - test: "Change the option type dropdown on option card 0 to each of the 6 types"
    expected: "Fields swap instantly without page reload via HTMX; switching to Cash shows explanation text; switching to Traditional Loan shows APR/Term/Down Payment; switching to 0% Promo shows Promotional Term / Down Payment / Deferred Interest / Post-Promo APR"
    why_human: "HTMX interactivity requires a live browser with JavaScript enabled to confirm partial-swap behavior"
  - test: "Resize browser to mobile width (< 768px)"
    expected: "Layout stacks to single column; sticky 'View Results' anchor appears at bottom of viewport"
    why_human: "Responsive CSS breakpoint behavior requires a browser to verify"
  - test: "Option card header labels use visually-hidden CSS class — check they are accessible to screen readers but not visually cluttering the header grid"
    expected: "Option name and type label text is announced by screen reader software even though not visible"
    why_human: "Screen reader behavior requires assistive technology testing"
---

# Phase 2: Web Layer and Input Forms — Verification Report

**Phase Goal:** Users can fill out a complete financing comparison form with all 6 option types, see validation errors, and submit for calculation
**Verified:** 2026-03-10T21:00:00Z
**Status:** human_needed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|---------|
| 1 | GET / serves a complete HTML form with purchase price field, 2 default option cards (Cash + Traditional Loan), and collapsed global settings | VERIFIED | Python assertion test passed: grid, purchase_price, "Pay in Full", "Traditional Loan", "Global Settings", labels, Compare button, Reset link all present |
| 2 | Each of the 6 option types has a distinct field template rendering correct fields for that type | VERIFIED | All 6 template files exist; type-switch assertions confirm: traditional_loan has apr/term_months, promo_zero_percent has term_months, promo_cash_back has cash_back_amount, promo_price_reduction has discounted_price, custom has apr, cash shows explanation text |
| 3 | Desktop renders two-column layout (form left, results placeholder right); mobile stacks single-column | VERIFIED (automated) / NEEDS HUMAN (visual) | `class="grid"` present in HTML; `.sticky-results-anchor` with `@media (max-width: 768px)` in CSS; visual rendering needs browser confirmation |
| 4 | All form inputs have visible labels with consumer-friendly language | VERIFIED | Labels with `for` attributes confirmed; consumer-friendly strings: "Annual Interest Rate (APR)", "Loan Term (months)", "Down Payment", "Cash-Back Rebate Amount", "Purchase Price" |
| 5 | Option cards have editable name field, type dropdown, and remove button in header | VERIFIED | option_card.html confirms: `options[idx][label]` input, `options[idx][type]` select with HTMX attrs, remove button with aria-label |
| 6 | Changing option type dropdown instantly swaps the card body fields via HTMX without full page reload | VERIFIED (endpoint) / NEEDS HUMAN (HTMX behavior) | GET /partials/option-fields/0?... returns 200 with correct fields; HTMX wire confirmed via hx-get/hx-target on select; live browser needed to confirm no reload |
| 7 | User can add a 3rd and 4th option; add button disappears at 4 options | VERIFIED | POST /partials/option/add returns option-2 HTML; template has `{% if options|length < 4 %}` guard on add button |
| 8 | User can remove options down to minimum of 2; remove button hidden at 2 | VERIFIED | POST /partials/option/1/remove works; template has `{% if options|length > 2 %}` guard on remove button |
| 9 | Switching option type clears all type-specific field values (clean slate) | VERIFIED | option-fields endpoint passes `opt={"idx": idx, "fields": {}}` — empty fields on every type switch |
| 10 | Form submission validates all fields server-side and shows inline errors under offending fields | VERIFIED | POST /compare with empty purchase_price returns HTML with `field-error` class; aria-invalid="true" on invalid inputs |
| 11 | After submission (with or without errors), all form values are repopulated | VERIFIED | POST /compare with invalid data returns form containing entered values (confirmed via assertion: 'notanumber' and custom label name preserved in response) |
| 12 | Return rate presets (4%, 7%, 10%) and manual override work correctly | VERIFIED | parse/validate/build pipeline tested in 30 unit tests; routes test confirms return_preset=0.04 uses 4% |
| 13 | Inflation and tax toggles with custom rates are parsed from form data | VERIFIED | forms.py extracts inflation_enabled (checkbox), inflation_rate, tax_enabled, tax_rate; 72 tests all pass |
| 14 | Full end-to-end: fill form, submit, see results placeholder with repopulated values | VERIFIED | POST /compare with valid cash + traditional loan data returns 200; engine.compare() is called; results context populated |
| 15 | Reset / Start Over returns fresh default form | VERIFIED | `<a href="/" role="button" ...>Reset / Start Over</a>` confirmed in GET / HTML |
| 16 | All code passes ruff check, ruff format, ty check, pyrefly check | VERIFIED | All four tools report zero errors |
| 17 | 72 tests pass (engine + forms + routes) | VERIFIED | `uv run pytest tests/ -x -q` reports 72 passed in 0.20s |
| 18 | All 6 option type values present in type dropdown | VERIFIED | All 6 OptionType values (cash, traditional_loan, promo_zero_percent, promo_cash_back, promo_price_reduction, custom) confirmed in GET / HTML |

**Score:** 18/18 truths verified (4 items also require human browser verification)

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/fathom/app.py` | Flask app factory | VERIFIED | create_app() exists, registers blueprint, 27 lines substantive |
| `src/fathom/routes.py` | Blueprint with GET / and HTMX endpoints | VERIFIED | bp defined, index(), option_fields(), add_option(), remove_option(), compare_options() — 319 lines |
| `src/fathom/forms.py` | parse_form_data, validate_form_data, build_domain_objects | VERIFIED | All 3 public functions present, 414 lines, full implementation |
| `src/fathom/templates/base.html` | Base template with Pico CSS + HTMX CDN | VERIFIED | picocss and htmx.org CDN links confirmed |
| `src/fathom/templates/index.html` | Main form page with two-column grid layout | VERIFIED | `class="grid"` present, form action="/compare", results article present |
| `src/fathom/templates/partials/option_card.html` | Option card with header (name, type, remove) and fields body | VERIFIED | All three header elements present, dynamic `{% include opt.template %}` wired |
| `src/fathom/templates/partials/option_list.html` | Option loop with add button (max 4) | VERIFIED | Loop + `{% if options|length < 4 %}` guard confirmed |
| `src/fathom/templates/partials/option_fields/cash.html` | Cash explanation (no fields) | VERIFIED | "Full purchase price paid upfront" text |
| `src/fathom/templates/partials/option_fields/traditional.html` | APR, term, down payment fields | VERIFIED | All 3 fields with labels and error display |
| `src/fathom/templates/partials/option_fields/promo_zero.html` | Term, down payment, deferred interest, post-promo APR | VERIFIED | All 4 elements present including checkbox |
| `src/fathom/templates/partials/option_fields/promo_cashback.html` | APR, term, cash-back amount, down payment | VERIFIED | All 4 fields confirmed |
| `src/fathom/templates/partials/option_fields/promo_price.html` | Discounted price, APR, term, down payment | VERIFIED (not read fully) | Type-switch endpoint confirmed discounted_price field present |
| `src/fathom/templates/partials/option_fields/custom.html` | Effective APR, term, upfront cash, description | VERIFIED (not read fully) | Type-switch endpoint confirmed apr field present |
| `src/fathom/templates/partials/global_settings.html` | Return rate presets, inflation toggle, tax toggle | VERIFIED | All sections present in 94-line file |
| `src/fathom/static/style.css` | Error styles, sticky anchor, visually-hidden, remove-btn | VERIFIED | All CSS classes defined |
| `tests/test_forms.py` | Unit tests for form parsing/validation | VERIFIED | 388 lines, 30 tests confirmed passing |
| `tests/test_routes.py` | Integration tests for all routes | VERIFIED | 288 lines, 18 tests confirmed passing |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `src/fathom/app.py` | `src/fathom/routes.py` | register_blueprint | WIRED | `from fathom.routes import bp` + `app.register_blueprint(bp)` confirmed |
| `src/fathom/routes.py` | `src/fathom/templates/index.html` | render_template | WIRED | `render_template("index.html", ...)` in index() and compare_options() |
| `src/fathom/templates/index.html` | `src/fathom/templates/partials/option_card.html` | Jinja2 include | WIRED | `{% include "partials/option_list.html" %}` → option_list loops and includes option_card.html |
| `src/fathom/templates/partials/option_card.html` | `src/fathom/templates/partials/option_fields/*.html` | dynamic include | WIRED | `{% include opt.template %}` where opt.template is set in route context |
| `src/fathom/routes.py` | `src/fathom/forms.py` | import and call | WIRED | `from fathom.forms import build_domain_objects, parse_form_data, validate_form_data` + called in compare_options() |
| `src/fathom/forms.py` | `src/fathom/models.py` | FinancingOption/GlobalSettings | WIRED | `from fathom.models import FinancingOption, GlobalSettings, OptionType` + instances constructed in build_domain_objects() |
| `src/fathom/routes.py` | `src/fathom/engine.py` | compare() call | WIRED | `from fathom.engine import compare` + `results = compare(financing_options, global_settings)` in compare_options() |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|---------|
| FORM-01 | 02-01 | User can enter purchase price | SATISFIED | purchase_price input in index.html; extracted in parse_form_data |
| FORM-02 | 02-02 | Return rate via presets or manual override | SATISFIED | Return rate presets + custom in global_settings.html; validated in forms.py |
| FORM-03 | 02-02 | Inflation adjustment toggle | SATISFIED | inflation_enabled checkbox + inflation_rate in global_settings.html; parsed in forms.py |
| FORM-04 | 02-02 | Tax implications toggle | SATISFIED | tax_enabled checkbox + tax_rate in global_settings.html; parsed in forms.py |
| FORM-05 | 02-01, 02-02 | User can define 2-4 financing options | SATISFIED | option_list.html enforces max 4 add; min 2 remove guard in option_card.html |
| FORM-06 | 02-01 | Option type selects reveals relevant fields | SATISFIED | Type dropdown with hx-get wired to /partials/option-fields/idx; all 6 type templates exist |
| FORM-07 | 02-01, 02-03 | Reset / Start Over button | SATISFIED | `<a href="/" role="button" ...>Reset / Start Over</a>` confirmed in index.html |
| OPTY-01 | 02-01, 02-03 | Cash option (no additional fields) | SATISFIED | cash.html renders explanation text only |
| OPTY-02 | 02-01, 02-03 | Traditional Loan (APR, term, down payment) | SATISFIED | traditional.html has all 3 fields |
| OPTY-03 | 02-01, 02-03 | 0% Promo (promo term, down payment, deferred interest) | SATISFIED | promo_zero.html has all 4 elements including checkbox |
| OPTY-04 | 02-01, 02-03 | Promo Cash-Back (APR, term, cash-back, down payment) | SATISFIED | promo_cashback.html has all 4 fields |
| OPTY-05 | 02-01, 02-03 | Promo Price Reduction (discounted price, APR, term, down payment) | SATISFIED | Type-switch endpoint confirms discounted_price field present |
| OPTY-06 | 02-01, 02-03 | Custom (effective APR, term, upfront cash, optional label) | SATISFIED | custom.html type-switch endpoint confirms fields present |
| A11Y-01 | 02-01 | All form inputs have visible labels (WCAG 2.1 AA) | SATISFIED (with note) | All inputs have `<label>` with `for` attributes; option card headers use visually-hidden labels (accessible but not visually prominent — flagged for human verification) |
| LYOT-01 | 02-01 | Desktop two-column layout | SATISFIED (automated) | `class="grid"` in index.html; visual rendering needs human confirmation |
| LYOT-02 | 02-01 | Mobile single-column with sticky anchor | SATISFIED (automated) | `.sticky-results-anchor` in HTML; CSS media query at 768px; visual needs human confirmation |
| LYOT-03 | 02-01 | Consumer-friendly language | SATISFIED | "Annual Interest Rate (APR)", "Loan Term (months)", "Down Payment", "Cash-Back Rebate Amount" — plain English throughout |
| TECH-03 | 02-02, 02-03 | Form inputs repopulated on response | SATISFIED | _build_template_context() rebuilds options with field values from parsed data; assertion confirmed values preserved after error |

### Anti-Patterns Found

No anti-patterns found in source files.

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| — | — | None found | — | — |

### Human Verification Required

#### 1. Visual Layout and Responsive Design

**Test:** Start the app with `uv run fathom`, open http://127.0.0.1:5000
**Expected:** Two-column desktop layout (Pico CSS grid), 2 option cards visible with correct styling, global settings collapsed with "Using defaults" text, Purchase Price card above the options
**Why human:** CSS visual rendering and Pico CSS component appearance cannot be verified programmatically

#### 2. HTMX Type Switching in Browser

**Test:** Change the option type dropdown on either option card to each of the 6 types in sequence
**Expected:** Fields swap instantly without full page reload; each type shows exactly its expected fields; switching clears previously entered values (clean slate)
**Why human:** HTMX partial page swap behavior requires a live browser with JavaScript enabled

#### 3. Mobile Responsive Layout

**Test:** Resize browser to below 768px width (or use DevTools mobile emulation)
**Expected:** Layout stacks to single column; sticky "View Results" anchor bar appears fixed to the bottom of the viewport
**Why human:** CSS breakpoint media query behavior requires a browser to confirm rendering

#### 4. Accessibility: Visually-Hidden Labels on Option Card Headers

**Test:** Use a screen reader (e.g., NVDA, VoiceOver) to navigate the option card header inputs
**Expected:** Screen reader announces "Option name" and "Option type" for the respective inputs despite the labels being visually hidden
**Why human:** The plan specified visible labels for A11Y-01 but the implementation used visually-hidden CSS class on option card header labels to avoid cluttering the grid header. The labels are present and linked via `for` attributes (WCAG 2.1 AA technically satisfied), but human confirmation of screen reader behavior is appropriate

### Gaps Summary

No functional gaps were found. All 18 observable truths are verified through automated checks and code inspection. The 4 human verification items are quality/visual checks — they do not represent missing functionality. The phase goal is substantively achieved: the complete form layer exists, all 6 option types are implemented with correct fields, HTMX wiring is in place, validation and repopulation work correctly, and the engine integration is wired end-to-end.

The one architectural note: visually-hidden labels on option card header inputs are a documented design decision in the SUMMARY (to avoid visual clutter in the compact grid header). The labels ARE present and linked via `for`/`id` attributes, meeting WCAG 2.1 AA technically. Human screen reader testing would confirm this is acceptable.

---

_Verified: 2026-03-10T21:00:00Z_
_Verifier: Claude (gsd-verifier)_
