# Phase 7: Dark Mode - Research

**Researched:** 2026-03-13
**Domain:** CSS theming, Pico CSS dark mode, SVG styling
**Confidence:** HIGH

## Summary

This phase is straightforward CSS work with no new dependencies. Pico CSS v2.1.1 (already vendored) has full built-in dark mode support via `prefers-color-scheme: dark` -- it automatically switches all `--pico-*` variables when the `<html>` element has no `data-theme` attribute. The current codebase forces light mode with `data-theme="light"` on `<html>`, so the primary enablement is removing that attribute.

The remaining work is converting ~15 hardcoded hex colors in `style.css` and ~10 hardcoded colors in SVG chart templates to use CSS custom properties with dark-mode variants. Since inline SVGs inherit page CSS, the same `@media (prefers-color-scheme: dark)` block handles both page elements and chart colors.

**Primary recommendation:** Remove `data-theme="light"` from base.html, add a single `@media (prefers-color-scheme: dark)` block in style.css for all custom color overrides, and replace hardcoded SVG colors with CSS variables.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Remove `data-theme="light"` from `<html>` in base.html -- let Pico CSS auto-detect via its built-in `prefers-color-scheme` CSS support
- Zero JavaScript needed for theme detection -- pure CSS approach
- No server-side theme detection (no client hints, no cookies)
- Use `@media (prefers-color-scheme: dark) {}` blocks in style.css for all custom color overrides
- Follow `--pico-*` variable namespace for overrides where Pico variables exist
- Create new `--pico-*` style variables only for colors Pico doesn't already cover
- Muted dark variants for all caveat types (warning, critical, info) -- dark desaturated backgrounds with lighter text
- Same approach for winner star and winner column highlight -- muted dark variants
- WCAG AA contrast ratios (4.5:1) are a hard requirement for light mode only
- Dark mode does not require WCAG AA compliance -- visual reasonableness is sufficient
- Replace hardcoded hex fills/strokes in SVG templates with CSS custom variables
- Use brighter/lighter variants of the 4 series colors in dark mode
- Pattern fill backgrounds (currently `fill="white"`) must flip to page background color via CSS variable
- Playwright tests must verify both light and dark themes using `emulateMedia`

### Claude's Discretion
- Specific hex values for all dark mode colors (caveats, accents, chart elements)
- Whether to define chart CSS variables in style.css or in a `<style>` block in the SVG templates
- Loading indicator styling in dark mode
- Any additional Pico variable overrides needed beyond the hardcoded colors identified

### Deferred Ideas (OUT OF SCOPE)
- None -- discussion stayed within phase scope
- DARK-04 (manual light/dark toggle) is deferred to v2 per REQUIREMENTS.md
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| DARK-01 | Application respects `prefers-color-scheme: dark` OS setting automatically | Removing `data-theme="light"` from base.html enables Pico's built-in auto-detection; Pico uses `@media (prefers-color-scheme:dark) { :root:not([data-theme]) }` selector |
| DARK-02 | All custom CSS overrides have dark-mode variants (no hardcoded light-only colors) | 15 hardcoded hex values identified in style.css; all can be overridden in a single `@media` block using CSS custom properties |
| DARK-03 | SVG chart colors are readable in both light and dark modes | Inline SVGs inherit page CSS; hardcoded colors in bar_chart.html and line_chart.html can be replaced with CSS variables that switch in the same `@media` block |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Pico CSS | 2.1.1 | Base CSS framework with dark mode | Already vendored; built-in dark mode via `prefers-color-scheme` when `data-theme` is absent |

### Supporting
No additional libraries needed. This is pure CSS work.

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Pure CSS `@media` | JavaScript `matchMedia()` | JS adds complexity; CSS-only is simpler and avoids flash-of-wrong-theme |
| CSS custom properties | Separate dark stylesheet | Single file is easier to maintain; `@media` blocks co-locate light and dark values |

## Architecture Patterns

### How Pico CSS Dark Mode Works (Verified)

Pico CSS uses three selector tiers:
1. **Forced light:** `:root:not([data-theme=dark])` and `[data-theme=light]` -- applies light colors
2. **Auto dark:** `@media (prefers-color-scheme:dark) { :root:not([data-theme]) }` -- applies dark colors when OS is dark AND no `data-theme` attribute exists
3. **Forced dark:** `[data-theme=dark]` -- applies dark colors regardless of OS

**Current state:** `<html data-theme="light">` matches tier 1, blocking auto dark mode.
**Target state:** `<html lang="en">` (no `data-theme`) -- allows tier 2 auto-switching.

Because Pico's dark mode and custom overrides both use `@media (prefers-color-scheme: dark)`, everything resolves in a single CSS render pass. No flash of light content occurs because:
- The browser evaluates `prefers-color-scheme` before first paint
- All CSS (Pico + custom) is in `<link>` tags in `<head>`, loaded synchronously
- No JavaScript is involved in theme detection

### Pattern: CSS Custom Properties for Theme-Aware Colors

**What:** Define colors as CSS custom properties at `:root` level, override in `@media (prefers-color-scheme: dark)`.
**When to use:** Any hardcoded color that needs a dark variant.
**Example:**
```css
/* Light mode defaults (at root level) */
:root {
  --chart-grid: #e5e7eb;
  --chart-label: #6b7280;
  --chart-bar-label: #374151;
  --chart-bg: #ffffff;
  --caveat-warning-bg: #fef3c7;
  --caveat-warning-text: #92400e;
  --caveat-warning-border: #f59e0b;
  /* ... etc */
}

/* Dark mode overrides */
@media (prefers-color-scheme: dark) {
  :root {
    --chart-grid: #374151;
    --chart-label: #9ca3af;
    --chart-bar-label: #d1d5db;
    --chart-bg: rgb(19, 22.5, 30.5); /* matches Pico dark bg */
    --caveat-warning-bg: #422006;
    --caveat-warning-text: #fbbf24;
    --caveat-warning-border: #d97706;
    /* ... etc */
  }
}
```

### Pattern: SVG Inheriting CSS Variables

**What:** Inline SVGs (rendered via Jinja) inherit CSS from the page. Replace hardcoded `fill` and `stroke` attributes with `var()` references.
**When to use:** Any SVG element that uses a color which should change in dark mode.
**Example (before):**
```html
<line stroke="#e5e7eb" stroke-width="0.5"/>
<text fill="#6b7280">$10,000</text>
```
**Example (after):**
```html
<line stroke="var(--chart-grid)" stroke-width="0.5"/>
<text fill="var(--chart-label)">$10,000</text>
```

**Important:** SVG pattern `fill="white"` backgrounds must use `var(--chart-bg)` so patterns render correctly against the dark page background.

### Recommendation: Define All Chart Variables in style.css

Chart CSS variables should be defined in `style.css` alongside all other custom properties, not in `<style>` blocks within SVG templates. Reasons:
- Single source of truth for all colors
- Easier to audit for dark mode coverage
- SVG templates stay focused on structure, not styling

### Anti-Patterns to Avoid
- **Duplicating Pico variables:** Do not redefine `--pico-background-color`, `--pico-color`, etc. Pico already handles these. Only create variables for colors Pico does not cover.
- **Using `data-theme` for testing:** Do not add `data-theme="dark"` for Playwright tests. Instead, use Playwright's `emulateMedia` which sets the CSS media feature directly, matching real user experience.
- **Hardcoding dark background in SVG:** Do not use `fill="rgb(19, 22.5, 30.5)"` in SVG templates. Use `var(--chart-bg)` so it adapts automatically.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Theme detection | JavaScript `matchMedia()` listener | CSS `@media (prefers-color-scheme: dark)` | Pure CSS avoids flash, simpler, no JS needed |
| Base UI dark mode | Custom dark variable overrides for forms, buttons, text | Pico CSS built-in dark mode | Pico handles ~100+ variables automatically |
| Dark color palette | Manual color picking | Systematic approach: desaturate + darken backgrounds, lighten text | Consistent, professional appearance |

## Common Pitfalls

### Pitfall 1: Flash of Light Content (FOUC)
**What goes wrong:** Page briefly shows light theme before switching to dark.
**Why it happens:** JavaScript-based theme detection, async CSS loading, or `data-theme` set after page load.
**How to avoid:** Pure CSS approach with `@media (prefers-color-scheme: dark)` in synchronously-loaded stylesheets. No JavaScript needed.
**Warning signs:** Light flash visible when loading page on dark-mode OS.

### Pitfall 2: Forgotten Hardcoded Colors
**What goes wrong:** Some elements stay light-colored in dark mode, creating jarring contrast.
**Why it happens:** Not auditing all hardcoded hex values in CSS and templates.
**How to avoid:** Systematic audit of all hex values. The complete list from CONTEXT.md:
- **style.css:** `#fef3c7`, `#fee2e2`, `#dbeafe` (caveat bg), `#92400e`, `#991b1b`, `#1e40af` (caveat text), `#f59e0b` (star/border), `rgba(59, 130, 246, 0.06)` (winner col)
- **SVG templates:** `#e5e7eb` (grid), `#6b7280` (axis labels), `#374151` (bar labels), `white` (pattern backgrounds)
- **charts.py:** `COLORS` array `["#2563eb", "#dc2626", "#059669", "#d97706"]` -- these are series colors passed to templates
**Warning signs:** Any `#` hex color or `rgb()`/`rgba()` value in CSS or HTML that is not wrapped in `var()`.

### Pitfall 3: SVG Pattern Backgrounds Not Flipping
**What goes wrong:** Bar chart patterns (hatched, dotted, crosshatch) use `fill="white"` for background. In dark mode, these create bright white rectangles inside bars.
**Why it happens:** Pattern `<rect>` elements have hardcoded `fill="white"`.
**How to avoid:** Replace `fill="white"` with `fill="var(--chart-bg)"` in all pattern definitions.
**Warning signs:** Bright white squares visible inside patterned bars in dark mode.

### Pitfall 4: Series Colors Too Dark in Dark Mode
**What goes wrong:** The 4 series colors (blue, red, green, orange) designed for white backgrounds become hard to see against dark backgrounds.
**Why it happens:** Colors optimized for light mode contrast.
**How to avoid:** Define brighter/lighter series color variants for dark mode. Keep the same hue family but increase lightness.
**Warning signs:** Chart lines/bars that blend into the dark background.

### Pitfall 5: Winner Column Background Invisible
**What goes wrong:** `rgba(59, 130, 246, 0.06)` winner column highlight is invisible on dark backgrounds (6% opacity blue on dark gray = no visible difference).
**Why it happens:** Very low opacity values designed for white backgrounds.
**How to avoid:** Use a higher opacity or different highlight approach in dark mode (e.g., `rgba(59, 130, 246, 0.15)`).
**Warning signs:** Winner column indistinguishable from non-winner columns in dark mode.

## Code Examples

### Complete Hardcoded Color Inventory

From the actual codebase, every hardcoded color that needs a dark variant:

**style.css (15 values):**
```css
/* Caveat backgrounds */
.caveat-warning { background: #fef3c7; }     /* needs dark variant */
.caveat-critical { background: #fee2e2; }     /* needs dark variant */
.caveat-info { background: #dbeafe; }         /* needs dark variant */

/* Caveat text */
.caveat-warning { color: #92400e; }           /* needs dark variant */
.caveat-critical { color: #991b1b; }          /* needs dark variant */
.caveat-info { color: #1e40af; }              /* needs dark variant */

/* Caveat borders */
.caveat-warning { border-left-color: #f59e0b; }  /* may keep or adjust */
.caveat-critical { border-left-color: #ef4444; }  /* may keep or adjust */
.caveat-info { border-left-color: #3b82f6; }      /* may keep or adjust */

/* Winner elements */
.winner-star { color: #f59e0b; }              /* needs dark variant */
.winner-col { background: rgba(59, 130, 246, 0.06); }  /* needs dark variant */

/* Savings color (has fallback) */
.savings { color: var(--pico-ins-color, #16a34a); }  /* Pico handles this */
```

**bar_chart.html (4 values):**
```html
stroke="#e5e7eb"        <!-- grid/axis line -->
fill="#374151"          <!-- bar name labels -->
fill="white"            <!-- pattern backgrounds (4 occurrences) -->
<!-- bar.color from Python is used for fill/stroke on bars and value labels -->
```

**line_chart.html (3 values):**
```html
stroke="#e5e7eb"        <!-- grid lines -->
fill="#6b7280"          <!-- axis labels -->
<!-- line.color from Python used for stroke and endpoint labels -->
```

### Playwright emulateMedia for Dark Mode Testing

```python
# Set dark mode preference
context = browser.new_context(
    viewport={"width": 1280, "height": 720},
    color_scheme="dark",  # Sets prefers-color-scheme: dark
)
page = context.new_page()

# Or toggle mid-test:
page.emulate_media(color_scheme="dark")
# ... verify dark mode rendering ...
page.emulate_media(color_scheme="light")
# ... verify light mode rendering ...
```

### SVG Pattern Fix Example

```html
<!-- Before: hardcoded white background -->
<pattern id="bar-pattern-hatched" width="10" height="10"
         patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
  <rect width="10" height="10" fill="white"/>
  <line x1="0" y1="0" x2="0" y2="10" stroke="currentColor" stroke-width="3"/>
</pattern>

<!-- After: CSS variable background -->
<pattern id="bar-pattern-hatched" width="10" height="10"
         patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
  <rect width="10" height="10" fill="var(--chart-bg, white)"/>
  <line x1="0" y1="0" x2="0" y2="10" stroke="currentColor" stroke-width="3"/>
</pattern>
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| JS `matchMedia()` + class toggle | CSS `prefers-color-scheme` media query | ~2020 (broad browser support) | No JS needed, no FOUC |
| Separate dark.css stylesheet | CSS custom properties + `@media` | ~2019 | Single file, co-located values |
| `data-theme` attribute switching | OS preference auto-detection | Ongoing | Better UX, respects user system settings |

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.x + Playwright 1.58+ |
| Config file | pyproject.toml `[tool.pytest.ini_options]` |
| Quick run command | `uv run pytest tests/ -x -q` |
| Full suite command | `uv run pytest tests/ && uv run python tests/playwright_verify.py` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| DARK-01 | OS dark mode auto-detected | Playwright | `uv run python tests/playwright_verify.py` (with dark mode section) | Needs update |
| DARK-02 | All custom CSS has dark variants | Playwright | Screenshot comparison in light/dark; verify no hardcoded hex in computed styles | Needs update |
| DARK-03 | SVG charts readable in dark mode | Playwright | Verify SVG text elements visible, chart elements have appropriate contrast | Needs update |

### Sampling Rate
- **Per task commit:** `uv run ruff check . && uv run ruff format --check .`
- **Per wave merge:** `uv run pytest tests/ -x -q && uv run python tests/playwright_verify.py`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/playwright_verify.py` -- needs new dark mode verification sections using `color_scheme="dark"` context
- [ ] Dark mode checks to add: page background color verification, caveat card visibility, SVG chart text legibility, winner column highlight visibility, pattern background color check

## Sources

### Primary (HIGH confidence)
- Pico CSS vendor file (`src/fathom/static/vendor/pico.min.css`) -- verified selector patterns for `prefers-color-scheme` and `data-theme`
- Existing codebase (`style.css`, `bar_chart.html`, `line_chart.html`, `charts.py`) -- complete hardcoded color inventory
- Playwright documentation (training data) -- `color_scheme` context option and `emulate_media` API

### Secondary (MEDIUM confidence)
- CSS `prefers-color-scheme` specification -- well-established, broad browser support since 2020

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- no new dependencies, Pico already handles dark mode
- Architecture: HIGH -- pure CSS approach verified against actual Pico CSS vendor file
- Pitfalls: HIGH -- all hardcoded colors inventoried from actual source files

**Research date:** 2026-03-13
**Valid until:** 2026-04-13 (stable -- CSS standards and Pico 2.x are mature)
