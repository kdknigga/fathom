# Requirements: Fathom

**Defined:** 2026-03-13
**Core Value:** Users can instantly see which financing option truly costs least when opportunity costs, inflation, and taxes are factored in — turning a complex financial comparison into a clear, plain-English recommendation.

## v1.1 Requirements

Requirements for v1.1 "Deeper Insights" milestone. Each maps to roadmap phases.

### Tooltips

- [ ] **TIPS-01**: User can see a `?` icon next to each form field that has financial jargon, and clicking/hovering reveals an explanation
- [ ] **TIPS-02**: User can see a `?` icon next to each result metric (True Total Cost, Opportunity Cost, Inflation Adjustment, etc.) with an explanation
- [ ] **TIPS-03**: Tooltips are accessible — keyboard-focusable, dismissable with Escape, hoverable without disappearing (WCAG 1.4.13)

### Tax Guidance

- [ ] **TAX-01**: User can expand a "What's my bracket?" reference below the tax rate field showing 2025 IRS brackets by filing status
- [ ] **TAX-02**: Tax bracket table shows income ranges for Single and Married Filing Jointly at all 7 federal rates (10%–37%)

### Input Polish

- [ ] **INPUT-01**: User can type or paste numbers with commas (e.g., "100,000") into any numeric field and the value is accepted
- [ ] **INPUT-02**: Numeric fields display comma-formatted values after the user leaves the field (blur formatting)
- [ ] **INPUT-03**: Server-side parsing strips commas before Decimal conversion — no silent failures

### Data Persistence

- [ ] **DATA-01**: User can click "Export" to download their current form inputs as a `.json` file
- [ ] **DATA-02**: User can upload a previously exported `.json` file to restore all form inputs
- [ ] **DATA-03**: Imported JSON is validated through the same Pydantic models as form submission — invalid files show an error message

### Dark Mode

- [ ] **DARK-01**: Application respects `prefers-color-scheme: dark` OS setting automatically
- [ ] **DARK-02**: All custom CSS overrides have dark-mode variants (no hardcoded light-only colors)
- [ ] **DARK-03**: SVG chart colors are readable in both light and dark modes

### Detailed Breakdown Table

- [ ] **DETAIL-01**: User can view a per-period (monthly/annual) cost breakdown for each financing option showing all cost factors (principal, interest, opportunity cost, inflation adjustment, tax savings)
- [ ] **DETAIL-02**: User can switch between options via tabs, with one tab per option
- [ ] **DETAIL-03**: User can view a "Compare" tab showing key totals side-by-side across all options per period
- [ ] **DETAIL-04**: User can toggle individual cost factor columns on/off
- [ ] **DETAIL-05**: Detailed breakdown table is accessible (proper table headers, scope attributes, ARIA labels)

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Visual Polish

- **PRINT-01**: Print-friendly CSS for results page
- **PDF-01**: Exportable PDF reports

### Scenarios

- **SCENE-01**: Save multiple parameter sets for side-by-side scenario comparison

### Dark Mode Enhancements

- **DARK-04**: Manual light/dark mode toggle button (override OS preference)

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Real-time comma formatting while typing | Cursor position bugs, mobile keyboard conflicts — format on blur only |
| Client-side JSON parse/restore | Violates server-side-only validation architecture |
| Tax bracket auto-calculation from income | Complex (filing status, deductions, state taxes) — wrong auto-computed rate creates false confidence |
| Downloadable amortization CSV/Excel | JSON export + detailed breakdown table cover the underlying need |
| Manual dark/light toggle | OS preference sufficient for v1.1; add in v1.2 if requested |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| TIPS-01 | Phase 9 | Pending |
| TIPS-02 | Phase 9 | Pending |
| TIPS-03 | Phase 9 | Pending |
| TAX-01 | Phase 9 | Pending |
| TAX-02 | Phase 9 | Pending |
| INPUT-01 | Phase 8 | Pending |
| INPUT-02 | Phase 8 | Pending |
| INPUT-03 | Phase 8 | Pending |
| DATA-01 | Phase 10 | Pending |
| DATA-02 | Phase 10 | Pending |
| DATA-03 | Phase 10 | Pending |
| DARK-01 | Phase 7 | Pending |
| DARK-02 | Phase 7 | Pending |
| DARK-03 | Phase 7 | Pending |
| DETAIL-01 | Phase 11 | Pending |
| DETAIL-02 | Phase 11 | Pending |
| DETAIL-03 | Phase 11 | Pending |
| DETAIL-04 | Phase 11 | Pending |
| DETAIL-05 | Phase 11 | Pending |

**Coverage:**
- v1.1 requirements: 19 total
- Mapped to phases: 19
- Unmapped: 0

---
*Requirements defined: 2026-03-13*
*Last updated: 2026-03-13 after roadmap creation*
