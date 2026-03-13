# Phase 7: Dark Mode - Context

**Gathered:** 2026-03-13
**Status:** Ready for planning

<domain>
## Phase Boundary

Application automatically adapts to OS `prefers-color-scheme: dark` setting with no visual regressions. All custom CSS and SVG charts render correctly in both light and dark modes. Manual light/dark toggle is deferred to v1.2 (DARK-04 in REQUIREMENTS.md).

</domain>

<decisions>
## Implementation Decisions

### Theme activation
- Remove `data-theme="light"` from `<html>` in base.html — let Pico CSS auto-detect via its built-in `prefers-color-scheme` CSS support
- Zero JavaScript needed for theme detection — pure CSS approach
- No server-side theme detection (no client hints, no cookies)

### CSS architecture
- Use `@media (prefers-color-scheme: dark) {}` blocks in style.css for all custom color overrides
- Follow `--pico-*` variable namespace for overrides where Pico variables exist
- Create new `--pico-*` style variables only for colors Pico doesn't already cover
- Since Pico handles the base theme via CSS and custom overrides use the same `@media` query, everything resolves in the same render pass — no flash of wrong theme

### Caveat card colors
- Muted dark variants for all caveat types (warning, critical, info) — dark desaturated backgrounds with lighter text
- Same approach for winner star and winner column highlight — muted dark variants, consistent treatment
- Color palette at Claude's discretion — will be reviewed in PR

### Accessibility
- WCAG AA contrast ratios (4.5:1) are a hard requirement for light mode only
- Dark mode does not require WCAG AA compliance — visual reasonableness is sufficient
- Dark mode should still be legible and usable, just not held to strict contrast ratios

### SVG chart adaptation
- Replace hardcoded hex fills/strokes in SVG templates with CSS custom variables (e.g., `fill="var(--chart-grid)"`)
- SVGs rendered inline in HTML inherit page CSS, so `@media (prefers-color-scheme: dark)` works for chart variables too
- Use brighter/lighter variants of the 4 series colors (blue, red, green, orange) in dark mode for better visibility against dark backgrounds
- Pattern fill backgrounds (currently `fill="white"`) must flip to the page background color via CSS variable — stroke/fill patterns stay in series color

### Testing
- Playwright tests must verify both light and dark themes
- Test both modes for: overall page rendering, caveat card visibility, SVG chart legibility, recommendation card, breakdown table
- Use Playwright's `emulateMedia` to toggle `prefers-color-scheme` between tests

### Claude's Discretion
- Specific hex values for all dark mode colors (caveats, accents, chart elements)
- Whether to define chart CSS variables in style.css or in a `<style>` block in the SVG templates
- Loading indicator styling in dark mode
- Any additional Pico variable overrides needed beyond the hardcoded colors identified

</decisions>

<specifics>
## Specific Ideas

No specific references — open to standard approaches. The goal is a native-feeling dark theme that doesn't look like an afterthought.

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- **Pico CSS v2.1.1** (`vendor/pico.min.css`): Has full built-in dark mode support — all `--pico-*` variables auto-switch when `data-theme` is not set
- **Custom style.css**: Already uses `var(--pico-*)` for most colors — only caveat cards, winner elements, and a few accents use hardcoded hex

### Established Patterns
- All colors in custom CSS use `var(--pico-*)` variables (good baseline) — only ~15 hardcoded hex values need dark variants
- SVG charts are server-rendered via Jinja templates with hardcoded colors in both Python (`charts.py` COLORS array) and HTML templates
- Bar chart patterns use `fill="white"` background + colored strokes for accessibility differentiation

### Integration Points
- `base.html` line 2: `data-theme="light"` — must be removed
- `style.css`: Add `@media (prefers-color-scheme: dark)` block for caveat, winner, and accent overrides
- `charts.py` line 24: `COLORS` array — may need dark variants passed to templates, OR replaced with CSS variables in SVG templates
- SVG templates (`bar_chart.html`, `line_chart.html`): Replace ~10 hardcoded hex fills/strokes with CSS variables
- Hardcoded colors to convert: `#fef3c7`, `#fee2e2`, `#dbeafe` (caveat bg), `#92400e`, `#991b1b`, `#1e40af` (caveat text), `#f59e0b` (star/border), `#e5e7eb` (grid), `#6b7280` (labels), `#374151` (bar labels), `rgba(59, 130, 246, 0.06)` (winner col)

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 07-dark-mode*
*Context gathered: 2026-03-13*
