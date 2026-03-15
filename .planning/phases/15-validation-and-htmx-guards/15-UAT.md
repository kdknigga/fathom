---
status: complete
phase: 15-validation-and-htmx-guards
source: [15-01-SUMMARY.md, 15-02-SUMMARY.md]
started: 2026-03-15T16:00:00Z
updated: 2026-03-15T16:10:00Z
---

## Current Test

[testing complete]

## Tests

### 1. Inflation Rate Validation Rejects Out-of-Bounds
expected: Enter an inflation rate above 20% (e.g., 25) with inflation enabled, then submit/trigger validation. An inline error message should appear near the inflation field, and the field should be marked with aria-invalid.
result: pass

### 2. Tax Rate Validation Rejects Out-of-Bounds
expected: Enter a tax rate above 60% (e.g., 75) with tax enabled, then submit/trigger validation. An inline error message should appear near the tax field, and the field should be marked with aria-invalid.
result: pass

### 3. Toggle-Off Disables Input Fields
expected: Uncheck the inflation toggle. The inflation rate input should become disabled (greyed out, not editable). Same behavior for the tax toggle disabling the tax rate input.
result: pass

### 4. Add Option Blocked at Maximum (4)
expected: With 4 financing options showing, click "Add Option". Instead of adding a 5th option, a warning banner appears saying "Maximum 4 options allowed" with role="alert" for screen readers. The option list remains unchanged.
result: pass

### 5. Remove Option Blocked at Minimum (2)
expected: With only 2 financing options showing, click remove on one. Instead of removing it, a warning banner appears saying "Minimum 2 options required" with role="alert". The option list remains unchanged.
result: pass

### 6. Normal Add/Remove Still Works
expected: With 3 options showing, clicking "Add Option" adds a 4th option. With 3 options showing, clicking remove on one removes it leaving 2. No warning banners appear for valid operations.
result: pass

## Summary

total: 6
passed: 6
issues: 0
pending: 0
skipped: 0

## Gaps

[none yet]
