---
phase: 07-dark-mode
verified: 2026-03-13T21:00:00Z
status: passed
score: 8/8 must-haves verified
re_verification: false
---

# Phase 7: Dark Mode Verification Report

**Phase Goal:** Application adapts to OS dark mode preference with no visual regressions
**Verified:** 2026-03-13
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| #   | Truth                                                                                                   | Status     | Evidence                                                                                                                        |
| --- | ------------------------------------------------------------------------------------------------------- | ---------- | ------------------------------------------------------------------------------------------------------------------------------- |
| 1   | User on dark-mode OS sees a dark-themed page automatically with no flash of light content               | VERIFIED   | `base.html` has no `data-theme` attribute; Pico CSS auto-switches via `@media (prefers-color-scheme: dark) { :root:not([data-theme]) }` |
| 2   | Caveat cards (warning, critical, info) are visible and legible in dark mode                             | VERIFIED   | All three caveat types use `var(--caveat-*-bg/text/border)` with deep muted dark overrides defined in `@media` block            |
| 3   | Winner star and winner column highlight are visible in dark mode                                        | VERIFIED   | `--winner-star-color: #fbbf24` and `--winner-col-bg: rgba(59,130,246,0.15)` defined in dark override block                     |
| 4   | Breakdown table sticky row-label column has correct background in dark mode                             | VERIFIED   | `.row-label` uses `var(--pico-background-color)` — Pico handles this automatically when no `data-theme` attribute              |
| 5   | SVG chart grid lines, axis labels, and bar name labels are legible in dark mode                         | VERIFIED   | `bar_chart.html` and `line_chart.html` use `var(--chart-grid)`, `var(--chart-label)`, `var(--chart-bar-label)` throughout      |
| 6   | SVG pattern fill backgrounds match the page background in dark mode (no bright white rectangles)        | VERIFIED   | Pattern backgrounds use `var(--chart-bg, white)`; `--chart-bg: var(--pico-background-color)` in dark override                  |
| 7   | Chart series colors (blue, red, green, orange) are visible against dark backgrounds                     | VERIFIED   | `--chart-series-0..3` overridden to brighter variants (#60a5fa, #f87171, #34d399, #fbbf24) in dark `@media` block              |
| 8   | Playwright tests verify both light and dark mode rendering                                              | VERIFIED   | `tests/playwright_verify.py` contains `verify_dark_mode()` and `verify_light_mode()` using `color_scheme` context option (6 occurrences) |

**Score:** 8/8 truths verified

### Required Artifacts

| Artifact                                                          | Expected                                          | Status   | Details                                                                                 |
| ----------------------------------------------------------------- | ------------------------------------------------- | -------- | --------------------------------------------------------------------------------------- |
| `src/fathom/templates/base.html`                                  | Theme auto-detection via Pico CSS                 | VERIFIED | Has `<html lang="en">` with no `data-theme` attribute (line 2)                          |
| `src/fathom/static/style.css`                                     | Dark mode CSS custom properties and overrides     | VERIFIED | `:root` defines 15 custom properties; `@media (prefers-color-scheme: dark)` block at line 27 |
| `src/fathom/templates/partials/results/bar_chart.html`            | Bar chart with CSS variable colors                | VERIFIED | 8 occurrences of `var(--chart-*)`; no hardcoded hex in color attributes                 |
| `src/fathom/templates/partials/results/line_chart.html`           | Line chart with CSS variable colors               | VERIFIED | 6 occurrences of `var(--chart-*)`; no hardcoded hex in color attributes                 |
| `tests/playwright_verify.py`                                      | Dark mode Playwright verification                 | VERIFIED | Contains `color_scheme` (6 occurrences), `verify_dark_mode()` and `verify_light_mode()` functions |

### Key Link Verification

| From                                              | To                                    | Via                                              | Status   | Details                                                                                  |
| ------------------------------------------------- | ------------------------------------- | ------------------------------------------------ | -------- | ---------------------------------------------------------------------------------------- |
| `src/fathom/static/style.css`                     | `src/fathom/static/vendor/pico.min.css` | Pico auto-switches when no `data-theme` attr   | VERIFIED | `@media (prefers-color-scheme: dark) { :root:not([data-theme]) }` at line 27-49          |
| `src/fathom/templates/partials/results/bar_chart.html` | `src/fathom/static/style.css`    | CSS variables `var(--chart-*)` in SVG attrs      | VERIFIED | 8 `var(--chart-` occurrences in bar_chart.html referencing variables defined in style.css |
| `src/fathom/templates/partials/results/line_chart.html` | `src/fathom/static/style.css`   | CSS variables `var(--chart-*)` in SVG attrs      | VERIFIED | 6 `var(--chart-` occurrences in line_chart.html referencing variables defined in style.css |

### Requirements Coverage

| Requirement | Source Plan | Description                                                          | Status    | Evidence                                                                            |
| ----------- | ----------- | -------------------------------------------------------------------- | --------- | ----------------------------------------------------------------------------------- |
| DARK-01     | 07-01       | Application respects `prefers-color-scheme: dark` OS setting automatically | SATISFIED | `data-theme` removed from `base.html`; Pico CSS `@media` block present in style.css |
| DARK-02     | 07-01       | All custom CSS overrides have dark-mode variants (no hardcoded light-only colors) | SATISFIED | 11 custom properties defined in `:root`; all caveat/winner/highlight rules use `var()`; only remaining `#16a34a` is an intentional Pico fallback for `var(--pico-ins-color)` |
| DARK-03     | 07-02       | SVG chart colors are readable in both light and dark modes           | SATISFIED | Chart templates use `var(--chart-series-N)`, `var(--chart-grid)`, `var(--chart-label)`, `var(--chart-bar-label)`, `var(--chart-bg)` with dark overrides; Playwright tests confirm |

**DARK-04** is explicitly out of scope (manual toggle button, deferred per REQUIREMENTS.md). No orphaned requirements.

### Anti-Patterns Found

None. The files modified in this phase were scanned for TODO/FIXME/placeholder comments, empty implementations, and stub handlers — none found.

One notable non-issue: `color: var(--pico-ins-color, #16a34a)` on line 156 of style.css. The `#16a34a` is a CSS fallback value for environments without Pico CSS, not a hardcoded override — this was explicitly noted in the plan as already handled by Pico and requires no dark variant.

### Human Verification Required

None. Per CLAUDE.md, all browser-based verification must use Playwright MCP. The Playwright tests in `tests/playwright_verify.py` (functions `verify_dark_mode` and `verify_light_mode`) automate all theme rendering checks including page background luminance, caveat card background detection, SVG chart text fill legibility, pattern background validation, and winner column highlight presence. 179 pytest tests pass. Ruff lint and format checks pass clean.

### Gaps Summary

No gaps. All must-haves from both plans are satisfied:

- Plan 07-01 (DARK-01, DARK-02): `data-theme` removed, 11 CSS custom properties defined with dark overrides, all custom CSS rules use `var()` references. Commits verified: `5b348fc`.
- Plan 07-02 (DARK-03): SVG chart templates fully converted to CSS variable references, brighter dark series colors defined, Playwright dark/light mode verification functions added. Commits verified: `cc1cb2b`, `5e35d45`.

---

_Verified: 2026-03-13_
_Verifier: Claude (gsd-verifier)_
