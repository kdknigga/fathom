# Requirements: Fathom v1.2

**Defined:** 2026-03-15
**Core Value:** Users can instantly see which financing option truly costs least when opportunity costs, inflation, and taxes are factored in.

## v1.2 Requirements

Requirements for code review defect fixes. Each maps to roadmap phases.

### Engine Correctness

- [x] **ENG-01**: Promo penalty modeling produces distinct costs for deferred-interest (retroactive) vs forward-only interest scenarios
- [x] **ENG-02**: Line chart plots cumulative true cost (payments + opportunity cost - tax savings + inflation) per period, not cumulative payments
- [x] **ENG-03**: Monetary rounding utility centralized into single `money.py` module, replacing 5 duplicate `quantize_money()` definitions

### Input Validation

- [ ] **VAL-01**: Inflation rate validated to 0-20% bounds with clear error message
- [ ] **VAL-02**: Tax rate validated to 0-60% bounds with clear error message
- [ ] **VAL-03**: HTMX add endpoint rejects adding beyond 4 options (returns unchanged form)
- [ ] **VAL-04**: HTMX remove endpoint rejects removing below 2 options (returns unchanged form)

### Custom Options

- [ ] **CUST-01**: Custom option's `custom_label` field is displayed in results as the option name
- [ ] **CUST-02**: Custom option's upfront cash field is clearly marked as optional in both UI and validation

### Test Coverage

- [x] **TEST-01**: Tests prove deferred-interest flags materially change `not_paid_on_time` results
- [x] **TEST-02**: Tests assert line chart data points match cumulative true cost metric
- [ ] **TEST-03**: Tests verify HTMX add-at-4 and remove-at-2 are rejected server-side
- [ ] **TEST-04**: Tests verify inflation/tax rate bounds reject impossible values
- [ ] **TEST-05**: Tests verify custom_label appears in rendered results

## Future Requirements

### UI Polish

- **UI-01**: Toggle-controlled inflation/tax field visibility (hide when toggles unchecked)
- **UI-02**: Browser test integration into automated pytest suite

## Out of Scope

| Feature | Reason |
|---------|--------|
| Live result updates as user types | Scratched from PRD — submit-driven HTMX is the design |
| Risk-weighted promo ranking | Intentional — optimistic paid-on-time ranking with caveat is correct |
| Browser test integration into pytest | Separate CI concern, not a code defect |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| ENG-01 | Phase 14 | Complete |
| ENG-02 | Phase 14 | Complete |
| ENG-03 | Phase 13 | Complete |
| VAL-01 | Phase 15 | Pending |
| VAL-02 | Phase 15 | Pending |
| VAL-03 | Phase 15 | Pending |
| VAL-04 | Phase 15 | Pending |
| CUST-01 | Phase 16 | Pending |
| CUST-02 | Phase 16 | Pending |
| TEST-01 | Phase 14 | Complete |
| TEST-02 | Phase 14 | Complete |
| TEST-03 | Phase 15 | Pending |
| TEST-04 | Phase 15 | Pending |
| TEST-05 | Phase 16 | Pending |

**Coverage:**
- v1.2 requirements: 14 total
- Mapped to phases: 14
- Unmapped: 0

---
*Requirements defined: 2026-03-15*
*Last updated: 2026-03-15 after roadmap creation*
