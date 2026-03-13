# Pitfalls Research

**Domain:** Flask/HTMX/Pico CSS SSR app — adding tooltips, complex interactive tables, JSON export/import, comma-formatted inputs, and dark mode to an existing v1.0 system
**Researched:** 2026-03-13
**Confidence:** HIGH (verified against official docs, MDN, WCAG spec, HTMX docs, Pico CSS source)

---

## Context: v1.0 Pitfalls Already Addressed

The original PITFALLS.md (researched 2026-03-10) covers v1.0 concerns: floating-point arithmetic, comparison period normalization, deferred interest, HTMX form state loss, and SVG accessibility. Those pitfalls are resolved and should not recur. This document covers only the new risk surface introduced by v1.1 features.

---

## Critical Pitfalls

### Pitfall 1: Comma-Formatted Inputs Break `_try_decimal()` Without Stripping

**What goes wrong:**
The existing `forms.py::_try_decimal()` calls `Decimal(value.strip())` directly. If a user types `1,500` into a comma-formatted input and submits the form, `Decimal("1,500")` raises `InvalidOperation` and returns `None`. The field silently fails validation as "empty" rather than as "invalid number." The user sees no error, the option is silently skipped or treated as zero, and results are wrong.

**Why it happens:**
`decimal.Decimal()` does not accept thousands separators. The constructor strictly requires strings like `"1500"` or `"1500.00"`. This is a silent failure — `InvalidOperation` is caught and swallowed, returning `None` — so the bad input never surfaces as an error message.

**How to avoid:**
Strip commas (and optionally spaces) before passing to `Decimal()`. Add a preprocessing step in `_try_decimal()`:
```python
value = value.strip().replace(",", "")
```
This must happen for every numeric field, not just the new comma-formatted ones — users will type commas in any number input once they see commas are accepted elsewhere. Add a test that submits `"1,500"` and verifies it parses as `Decimal("1500")`.

**Warning signs:**
- A field shows no error but the result is obviously wrong (missing a factor of 1000)
- Submitting `10,000` as purchase price causes results to show as if price were 0 or empty
- No validation error appears for malformed comma input

**Phase to address:**
Phase 1 (Comma-normalized inputs) — before any form field gets the comma-display treatment.

---

### Pitfall 2: `input[type="number"]` Cannot Display Commas

**What goes wrong:**
The current form likely uses `<input type="number">` for numeric fields. If you add comma formatting via JavaScript while keeping `type="number"`, the browser rejects the comma-containing value as invalid and sends an empty string to the server. The JavaScript-formatted display and the browser's internal value are in conflict.

**Why it happens:**
`type="number"` has a strict value model: only numeric characters and `.` are valid. Commas are not valid in the HTML number input value. The browser will not submit a number input whose display value contains commas.

**How to avoid:**
Switch comma-formatted fields to `type="text"` with `inputmode="numeric"` (or `inputmode="decimal"` for fields that accept decimals). This gives mobile users the numeric keyboard while allowing the value to contain commas. The server must handle the comma-stripped parsing regardless (see Pitfall 1).

**Warning signs:**
- Comma-formatted inputs submit as empty strings on form post
- Browser developer tools show the input's `.value` as `""` when display shows `"1,500"`
- Chrome / Firefox behave differently because they have different tolerance for invalid `type="number"` values

**Phase to address:**
Phase 1 (Comma-normalized inputs) — must be done at the same time as the comma JavaScript, not after.

---

### Pitfall 3: FOUC (Flash of Unstyled Content) on Dark Mode Initial Load

**What goes wrong:**
If dark mode is implemented purely via CSS `prefers-color-scheme`, the page loads correctly on first visit. But if a user-override toggle is added later (stored in `localStorage`), and the toggle is implemented by setting `data-theme` via JavaScript after page load, users who have toggled to dark mode see a white flash before the page goes dark on every subsequent load.

**Why it happens:**
The browser renders the initial HTML (with `data-theme="light"` hardcoded in `base.html`) immediately, before JavaScript executes. The JavaScript then reads `localStorage` and changes `data-theme` to `"dark"`. The gap between first paint and JavaScript execution causes the white flash.

**How to avoid:**
For CSS-only `prefers-color-scheme` (no user override toggle), FOUC does not occur — the CSS media query is evaluated before paint. If v1.1 only adds `prefers-color-scheme` support without a toggle button, this pitfall does not apply.

If a toggle button is added: remove the hardcoded `data-theme="light"` from `<html>` and add a blocking inline `<script>` in `<head>` (before the CSS links) that reads `localStorage` and sets `data-theme` synchronously:
```html
<script>
  (function() {
    var t = localStorage.getItem('fathom-theme');
    if (t) document.documentElement.setAttribute('data-theme', t);
  })();
</script>
```
This script must be inline (not in an external file) and must appear before any `<link rel="stylesheet">` tags. The Pico CSS GitHub issues tracker explicitly identifies this pattern as the fix for FOUC.

**Warning signs:**
- Users with dark mode toggled see white flash on every page load
- The flash is present on desktop but not mobile (mobile renders faster before JS executes, but the same race exists)
- Dark mode preference is lost after HTMX partial page updates replace `<html>` element attributes

**Phase to address:**
Phase 5 (Dark mode) — only relevant if a user override toggle is implemented alongside `prefers-color-scheme`.

---

### Pitfall 4: SVG Charts Use Hardcoded Hex Colors That Are Invisible in Dark Mode

**What goes wrong:**
`charts.py` defines `COLORS = ["#2563eb", "#dc2626", "#059669", "#d97706"]`. In dark mode these colors remain usable (they are saturated enough to show on dark backgrounds), but any chart text, axis lines, grid lines, or annotation colors that are hardcoded as `"#333"` or `"#000000"` become invisible against a dark background. The Pico CSS CSS variables (`--pico-color`, `--pico-muted-color`) adapt automatically; hardcoded hex in SVG attributes do not.

**Why it happens:**
SVG attributes (`fill="#333"`, `stroke="#000"`) are not CSS properties and do not inherit from the CSS cascade. They are hardcoded values that ignore `prefers-color-scheme` and `data-theme`. Only SVG elements whose colors are expressed as `currentColor` or CSS variables pick up theme changes.

**How to avoid:**
In the SVG Jinja templates (not `charts.py` — that generates data, not markup), replace any hardcoded color values for text, axes, and grid lines with `currentColor` or CSS custom properties:
- Axis labels: `fill="currentColor"` instead of `fill="#333"`
- Grid lines: `stroke="currentColor"` instead of `stroke="#ccc"`
- Chart border: `stroke="currentColor"` instead of `stroke="#000"`

The data series colors (`#2563eb`, etc.) can remain hardcoded because they are already saturated enough for both modes, and changing them risks breaking the established pattern/color accessibility system.

After implementing dark mode, visually check the charts in both themes via Playwright screenshot comparison.

**Warning signs:**
- Chart axis labels disappear in dark mode (black text on dark background)
- Grid lines are invisible in dark mode
- Chart legend text is unreadable

**Phase to address:**
Phase 5 (Dark mode) — survey all SVG templates for hardcoded color attributes before shipping.

---

### Pitfall 5: HTMX Partial Updates Overwrite `data-theme` on `<html>` or `<body>`

**What goes wrong:**
HTMX swaps in partial HTML fragments. If any HTMX response includes a `<html>` or `<body>` tag (which can happen if a route accidentally returns the full page for an HTMX request), HTMX replaces the entire document, wiping the `data-theme` attribute the user set. The user's dark mode preference disappears mid-session.

**Why it happens:**
HTMX partial responses should never include document-level tags. But it is easy to accidentally return a full page from a route if the HTMX header check is missing (`if is_htmx: return partial else: return full`). Dark mode state is stored on the root `<html>` element, so any replacement of that element resets it.

**How to avoid:**
Ensure every HTMX-facing route returns only the fragment, never a full page. This is already the pattern in `routes.py` (`is_htmx` checks are present), so the risk is in new routes added for v1.1 features (table endpoint, export/import endpoint) forgetting this check.

Additionally, dark mode state stored in `localStorage` and applied via the inline head script is self-healing: even if `data-theme` is briefly overwritten, the script will not re-run on a partial update. Add an `htmx:afterSwap` event listener that re-applies the stored theme to the `<html>` element:
```javascript
document.body.addEventListener('htmx:afterSwap', function() {
  var t = localStorage.getItem('fathom-theme');
  if (t) document.documentElement.setAttribute('data-theme', t);
});
```

**Warning signs:**
- Clicking "Calculate" reverts to light mode mid-session
- Any HTMX request resets the theme

**Phase to address:**
Phase 5 (Dark mode), but also review in any phase that adds new HTMX routes.

---

### Pitfall 6: HTMX Cannot Swap `<tr>` or `<td>` Fragments Directly

**What goes wrong:**
The detailed breakdown table will likely need HTMX for tab switching and column toggles. If a tab-switch HTMX request returns a `<tbody>` or `<tr>` fragment, HTMX may fail to insert it correctly because the HTML spec disallows table row/cell elements as standalone DOM children outside of a `<table>` context. HTMX parses the response via `innerHTML`, and the browser immediately re-parents or discards these elements.

**Why it happens:**
This is documented in the HTMX GitHub issues as "Troublesome Tables." When HTMX temporarily inserts a fragment as innerHTML of a container, the browser's HTML parser enforces table structure rules and moves elements to unexpected locations.

**How to avoid:**
Wrap bare table fragments in a `<template>` tag in the response, or wrap the entire `<table>` and use `outerHTML` swap on the table element rather than swapping only rows. An alternative is to wrap the swappable section in a `<div>` inside the table using `<tr><td colspan="N"><div id="swap-target">...</div></td></tr>`, so the swap target is a `<div>` not a table element.

The simplest safe approach for the breakdown table: make the HTMX target the `<div>` that contains the `<table>`, not the table or rows themselves.

**Warning signs:**
- Tab switching in the breakdown table seems to work but rows appear in wrong columns
- Browser inspector shows rows moved outside the table element
- The table renders correctly on initial load but breaks after any HTMX swap

**Phase to address:**
Phase 2 or 3 (Detailed breakdown table) — must be designed with this constraint from the start, not fixed after.

---

### Pitfall 7: JSON Import Accepting Arbitrary Pydantic Input Without Size or Content Limits

**What goes wrong:**
A JSON import endpoint that passes the uploaded JSON directly to Pydantic model parsing has two risks: (1) a multi-megabyte JSON file causes the server to attempt to parse and validate an enormous payload before returning an error, and (2) deeply nested or malformed JSON that is valid JSON but maximally expensive to validate (e.g., lists with thousands of elements for fields expecting a single value) can cause slow responses or memory pressure.

**Why it happens:**
Developers trust Pydantic's validation to reject invalid data, which it does — but Pydantic validates after parsing. Python's `json.loads()` will parse any valid JSON regardless of size. The Pydantic model may add field length limits, but without a size cap on the raw request, the parse step is unbounded.

**How to avoid:**
Add an explicit file size limit before calling `json.loads()`. Flask's `request.content_length` and `MAX_CONTENT_LENGTH` config key can enforce this. Since the exported JSON contains only form inputs (purchase price, 2–4 financing options, global settings), a legitimate file will never exceed 10KB. Reject anything larger:
```python
MAX_IMPORT_BYTES = 10_240  # 10 KB
if request.content_length and request.content_length > MAX_IMPORT_BYTES:
    return error_response("File too large")
```

Also validate the top-level JSON structure before passing to Pydantic: confirm the root is a dict, not a list or primitive. This prevents Pydantic from attempting to coerce unexpected types.

**Warning signs:**
- Import endpoint takes > 100ms for even small files (indicates excessive parsing)
- No size limit is visible in the route code

**Phase to address:**
Phase 4 (JSON export/import) — build the limit in from the start, not as a follow-up.

---

### Pitfall 8: JSON Export Triggers a Full Page Reload or an HTMX Partial Swap Instead of a Download

**What goes wrong:**
If the JSON export endpoint returns JSON with the standard `Content-Type: application/json` and no `Content-Disposition: attachment` header, the browser navigates to the URL and displays the raw JSON, or HTMX intercepts the response and tries to swap it into the DOM. Neither is the desired behavior (triggering a file download).

**Why it happens:**
Browsers only trigger a file download when the response has `Content-Disposition: attachment`. Without it, `application/json` responses are displayed inline in the browser. HTMX intercepts all responses from elements it controls and applies its swap logic unless told otherwise.

**How to avoid:**
For the export endpoint, use `hx-boost="false"` on the export button/link so HTMX does not intercept the request. Use a plain `<a>` download link or a form with `target="_blank"` to bypass HTMX entirely. On the server, use `flask.send_file()` or construct the response with explicit headers:
```python
response = make_response(json_data)
response.headers["Content-Type"] = "application/json"
response.headers["Content-Disposition"] = 'attachment; filename="fathom-scenario.json"'
```

An alternative that avoids a server round-trip entirely: generate the JSON client-side via JavaScript and trigger a download using `URL.createObjectURL()`. This works cleanly for a stateless app where the server already gave the browser all the form state.

**Warning signs:**
- Clicking "Export" navigates away from the page
- Clicking "Export" shows raw JSON in the browser tab
- HTMX throws a swap error because it received JSON instead of HTML

**Phase to address:**
Phase 4 (JSON export/import) — the download mechanism must be explicit in the design.

---

### Pitfall 9: Tooltip WCAG 1.4.13 — Hover-Only Content That Fails Persistence, Hoverable, or Dismissable

**What goes wrong:**
A CSS-only tooltip (`:hover` pseudo-class, no JavaScript) passes the basic "shows on hover" requirement but fails three WCAG 2.1 AA criteria under SC 1.4.13 (Content on Hover or Focus):
1. **Not dismissable**: Users with screen magnification who accidentally trigger a tooltip cannot dismiss it without moving away (no Escape key support in CSS-only).
2. **Not hoverable**: The tooltip disappears if the pointer moves from the trigger to the tooltip content itself — meaning users cannot hover over the tooltip to read it at their own pace.
3. **Not keyboard accessible**: Screen reader and keyboard users cannot trigger `:hover` tooltips via focus.

**Why it happens:**
CSS-only tooltips are seductive because they have zero JavaScript and appear to "just work." They satisfy the basic visual requirement but are not WCAG 2.1 AA compliant by themselves.

**How to avoid:**
Use the native HTML Popover API (`popover` attribute) or a small amount of JavaScript for tooltip behavior. The Popover API provides:
- Keyboard accessibility (triggers on focus)
- Escape key dismiss (built into the browser)
- Ability to hover over tooltip content without dismissal

Minimal required behavior:
- Tooltip triggers on both `mouseover` and `focusin` events
- Tooltip is linked to its trigger via `aria-describedby`
- Tooltip text is also available in the form label or accessible name (tooltip is supplementary, not the sole carrier of required information)
- Tooltip stays visible when the pointer moves into the tooltip itself
- Pressing Escape dismisses the tooltip

**Warning signs:**
- Tooltip disappears immediately when pointer moves from `?` icon toward tooltip text
- Tab-focusing the `?` icon does not show the tooltip
- Pressing Escape has no effect on visible tooltip
- Axe or WAVE accessibility audit flags tooltip triggers

**Phase to address:**
Phase 1 (Input tooltips) and Phase 2 (Output tooltips) — get the accessibility pattern right on the first tooltip, not after implementing all of them.

---

### Pitfall 10: Tooltip z-index Clipped by Overflow or Stacking Context

**What goes wrong:**
Tooltips appearing inside table cells, grid cells, or form cards may be clipped or hidden if any ancestor element has `overflow: hidden`, `overflow: auto`, or creates a CSS stacking context (via `position: relative; z-index: N` or `transform`). The tooltip renders but is invisible because it is cropped by the ancestor's overflow boundary.

**Why it happens:**
Pico CSS sets various `overflow` and positioning properties on its card and grid components. A tooltip positioned absolutely inside a Pico CSS `<article>` or `<fieldset>` may be clipped before it exits the parent's bounds.

**How to avoid:**
Use the HTML Popover API. Popovers render in the "top layer" — a browser-native rendering layer above all stacking contexts and overflow clipping. This makes `z-index` and `overflow` issues irrelevant for popover-based tooltips. If using CSS-only positioning instead, the tooltip element must be positioned relative to the `<body>` or a non-overflow-hidden ancestor, which is fragile.

**Warning signs:**
- Tooltip is partially visible near the edge of a card but cut off
- Tooltip appears in one section (global settings) but is clipped in another (option cards)
- Inspector shows the tooltip element in the DOM but it is hidden visually

**Phase to address:**
Phase 1 (Input tooltips) — choose the implementation approach (Popover API vs. CSS-only) before writing any tooltip HTML.

---

### Pitfall 11: Tab State in the Breakdown Table Not Reflected in URL, Lost on HTMX Swap

**What goes wrong:**
If the breakdown table's active tab (e.g., "Option A Detail", "Option B Detail", "Compare All") is tracked only in client-side state (CSS class on the active tab button), and the Calculate button triggers an HTMX swap that replaces the results section, the active tab resets to the default tab. Users who are looking at the "Compare All" tab, change an input, and click Calculate, lose their tab position.

**Why it happens:**
HTMX replaces the target DOM fragment with fresh server-rendered HTML. The server does not know which tab was active (it was only a CSS class in the browser). The fresh HTML always renders the first tab as active.

**How to avoid:**
Pass the active tab state back to the server with the Calculate request. Add a hidden input (or use `hx-include` on a data attribute) that tracks the currently active tab name. The server includes this in the template context so the correct tab is rendered as active.

Alternatively, use an HTMX `hx-on::after-settle` event to re-activate the last-known tab from a JavaScript variable, but this is more fragile than the server-echo approach.

**Warning signs:**
- Active tab resets to "Option A" every time Calculate is clicked
- Changing an input while on "Compare All" tab causes the view to jump back to the first tab

**Phase to address:**
Phase 2 or 3 (Detailed breakdown table) — design tab state persistence before building the tab UI.

---

### Pitfall 12: Column Toggles in Breakdown Table Sent as Unchecked Checkboxes (Missing From POST)

**What goes wrong:**
HTML checkboxes that are unchecked are not included in form POST data. If column visibility toggles are implemented as checkboxes, the server receives only the names of checked (visible) columns, and must infer that absent names mean hidden. This is the correct interpretation, but it is easy to accidentally code the inverse logic: "if the checkbox name is present, hide the column."

**Why it happens:**
This is a well-known HTML forms gotcha. Developers testing always check at least one checkbox and never test the case where all checkboxes are unchecked, so the absent-means-unchecked behavior is not noticed until a user unchecks everything.

**How to avoid:**
Be explicit in the server code: the set of visible columns is the set of column names present in the POST data for the toggle checkboxes. Document this clearly. Test: send a request with no column toggles checked and verify the server correctly renders an empty (or minimum-column) table, not a full table.

Alternatively, use `hx-vals` or hidden inputs to explicitly send the toggle state as `true`/`false` strings instead of relying on checkbox presence/absence.

**Warning signs:**
- Unchecking all column toggles shows all columns instead of none
- Column toggle behavior works for checking but not for unchecking
- "I unchecked this but it's still showing" user reports

**Phase to address:**
Phase 3 (Column toggles in breakdown table) — write the server-side column selection logic with explicit tests for the unchecked case.

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| CSS-only tooltips (`::after` pseudo-elements) | Zero JavaScript, simple to implement | Not WCAG 1.4.13 AA compliant; fails keyboard and dismiss requirements | Never for public-facing accessibility-required app |
| Comma formatting only on the display (not the stored value) | Simpler JS — format on blur, strip on submit | If stripping ever breaks or is bypassed, Decimal() receives invalid input silently | Never — always strip in the server-side parser as the authoritative path |
| Dark mode toggle storing preference as a URL parameter | No localStorage complexity | Users must re-apply preference on every visit; URLs become unshare-able | Never — use localStorage |
| Rendering the full breakdown table server-side on every Calculate | No additional HTMX complexity for tabs | 300ms budget risk if table has 60+ rows × 4 options × multiple cost factors | Acceptable if rendering is fast; test with max data before committing |
| JSON export via server round-trip when all data is in the form | Consistent with SSR philosophy | Extra network round-trip; server must reconstruct data it already sent | Acceptable; clean architecture, negligible latency |

---

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| HTMX + file download (JSON export) | HTMX intercepts the download request and tries to swap JSON into the DOM | Use `hx-boost="false"` on the download link, or use a plain `<a>` tag pointing to the export URL with `download` attribute |
| HTMX + file upload (JSON import) | Submitting a file input via HTMX requires `hx-encoding="multipart/form-data"` | Set `hx-encoding="multipart/form-data"` on the form or element; without it, Flask receives no file data |
| Pico CSS dark mode + custom CSS variables | Custom CSS variables in `style.css` do not automatically get dark mode variants | Define separate `[data-theme="dark"]` overrides for every custom CSS variable, or use only Pico's built-in variables |
| HTMX + Pico CSS loading indicator | Pico CSS uses `aria-busy="true"` for loading states; HTMX uses `.htmx-indicator` class | Choose one pattern; using both means the UI may show double indicators or neither during requests |
| JavaScript comma formatting + HTMX form submission | JS comma-formatting the input value on `blur` then HTMX including the input value on `input` (before blur fires) | Listen on `htmx:configRequest` event to strip commas from all numeric values before HTMX sends the request |

---

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Breakdown table with period-by-period rows × 4 options × 8+ cost factors | Jinja renders slowly; large HTML payload; browser table layout triggers reflow | Benchmark with 60-month comparison × 4 options before committing to full table expansion; paginate or collapse by default | At 60 months × 4 options × 8 factors = 1,920 table cells in one HTMX response |
| Comma formatting on every keystroke via JavaScript `input` event | Input lag on older devices, particularly mobile | Debounce the formatting or format only on `blur` | At any significant volume on low-end mobile |
| JSON import parsing before size check | Server blocks on large file parsing | Check `content_length` before `json.loads()` | Any file over ~100KB; legitimate exports are under 5KB |

---

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| JSON import without schema validation — passing raw parsed dict to application code | Attacker-crafted JSON with unexpected field types (e.g., list where string expected) causes unhandled exceptions leaking stack traces | Always pass imported JSON through the Pydantic model validation pipeline used for form data; never trust the schema of uploaded JSON |
| Rendering imported JSON field values directly into HTML without escaping | XSS via crafted `label` or `custom_label` fields in the imported JSON | Jinja2 auto-escaping handles this for `{{ value }}`, but verify no `{{ value | safe }}` is used anywhere in the templates that render option names |
| Exposing server-generated filename in Content-Disposition with user-controlled content | Path traversal or header injection via filename containing `../` or newlines | Use a fixed, non-user-influenced filename like `"fathom-scenario.json"` — never derive the download filename from any user input |

---

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Tooltip text that restates the label ("APR: The APR field") | Users dismiss tooltips as useless, stop reading them | Write tooltips that add meaning the label cannot carry: "The annual interest rate your lender charges. Promotional 0% offers have APR=0 only during the promo period." |
| Tax rate guidance that gives a number without explaining how to find yours | Users pick a wrong rate and get inaccurate results | Link to IRS tax bracket table, explain "use your marginal rate — the rate on your last dollar of income, not your effective rate" |
| Breakdown table defaulting to the full period-by-period view | Overwhelming wall of numbers on first encounter | Default to the summary row or first-tab view; expand to period detail on demand |
| Dark mode toggle that applies only to the results section but not the form | Jarring split-screen appearance | Apply `data-theme` to `<html>`, never to individual sections |
| JSON import that silently discards unknown fields | Users who manually edit the JSON and misspell a key see no error | Log or surface a warning when unknown fields are present, even if Pydantic's `model_config = ConfigDict(extra="ignore")` swallows them silently |

---

## "Looks Done But Isn't" Checklist

- [ ] **Comma inputs — server parse:** Submit `"1,500"` to each numeric field via form POST; verify server receives `Decimal("1500")`, not `None` or an error
- [ ] **Comma inputs — all browsers:** Verify comma input behavior in Chrome, Firefox, and Safari; all must display and submit correctly
- [ ] **Tooltips — keyboard:** Tab to every `?` icon; verify tooltip appears on focus and dismisses on Escape
- [ ] **Tooltips — hover-to-content:** Move pointer from `?` icon onto tooltip text; verify tooltip stays visible
- [ ] **Tooltips — no overflow clipping:** Check every tooltip location (global settings, each option card, results section) for z-index/overflow clipping
- [ ] **Dark mode — SVG charts:** Screenshot charts in dark mode; verify axis labels, grid lines, and text are visible (not black-on-dark)
- [ ] **Dark mode — custom CSS variables:** Confirm every variable in `style.css` has a dark mode counterpart or uses Pico built-in variables that already do
- [ ] **Dark mode — HTMX does not reset theme:** Trigger a Calculate request while in dark mode; confirm the page stays dark after the HTMX swap
- [ ] **HTMX table swap:** Tab-switch in the breakdown table returns valid HTML; verify no stray `<tr>` or `<td>` elements appear outside the table
- [ ] **JSON export:** Click export; confirm browser downloads a `.json` file (not navigates to raw JSON); confirm the page does not reload
- [ ] **JSON import:** Upload the exported file; confirm form fields repopulate exactly
- [ ] **JSON import — malformed input:** Upload a non-JSON file and a too-large file; verify graceful error messages, no 500 errors
- [ ] **Column toggles — unchecked state:** Uncheck all column toggles; verify server handles empty checkbox POST without displaying all columns
- [ ] **Tab state persistence:** Select "Compare All" tab, change an input, click Calculate; verify the "Compare All" tab is still active after update

---

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Comma input breaking `_try_decimal()` | LOW | One-line fix in `_try_decimal()`; add test; deploy |
| CSS-only tooltips needing WCAG retrofit | MEDIUM | Replace `:hover` CSS with Popover API or JavaScript; test all tooltip locations |
| FOUC on dark mode toggle | LOW | Add inline head script; no other changes required |
| SVG chart colors invisible in dark mode | LOW–MEDIUM | Audit SVG templates; replace `fill="[hex]"` text/axis colors with `currentColor`; Playwright screenshot test |
| HTMX resetting dark mode | LOW | Add `htmx:afterSwap` listener; 3 lines of JavaScript |
| HTMX table fragment swap failures | MEDIUM | Restructure HTMX target from table element to wrapper `<div>`; update all tab-switch endpoints |
| JSON import without size limit | LOW | Add 10KB check before `json.loads()`; one-line change |
| JSON export not triggering download | LOW | Add `hx-boost="false"` or switch to plain `<a>` tag |

---

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Comma inputs breaking `_try_decimal()` | Phase 1: Comma-normalized inputs | Test: POST `"1,500"` → server returns `Decimal("1500")` |
| `input[type="number"]` rejecting comma values | Phase 1: Comma-normalized inputs | Browser dev tools: input value is correct string before HTMX sends |
| HTMX + file upload encoding | Phase 4: JSON export/import | Playwright: upload file, verify form populates |
| JSON import size/schema safety | Phase 4: JSON export/import | Test: upload 100KB file → 413 error; upload `[]` (array root) → validation error |
| JSON export not downloading | Phase 4: JSON export/import | Playwright: click export, verify file download dialog |
| Tooltip WCAG 1.4.13 compliance | Phase 1: Input tooltips (first tooltip sets the pattern) | Axe audit; keyboard navigation test; hover-to-content test |
| Tooltip overflow/z-index clipping | Phase 1: Input tooltips | Visual check in every section; screenshot each tooltip location |
| SVG chart dark mode | Phase 5: Dark mode | Playwright screenshot in both themes; check axis label visibility |
| FOUC on dark mode toggle | Phase 5: Dark mode | Load page in dark-mode-toggled state; verify no white flash |
| HTMX resetting `data-theme` | Phase 5: Dark mode | Toggle dark, click Calculate, verify theme preserved |
| HTMX table swap with `<tr>` fragments | Phase 2/3: Breakdown table | Playwright: click tab, verify table renders correctly |
| Tab state lost after Calculate | Phase 2/3: Breakdown table | Playwright: select tab, click Calculate, verify tab still active |
| Checkbox POST absent-means-unchecked | Phase 3: Column toggles | Test: POST with no toggles checked → server returns minimum-column table |

---

## Sources

- MDN: [prefers-color-scheme](https://developer.mozilla.org/en-US/docs/Web/CSS/@media/prefers-color-scheme)
- Pico CSS: [Color Schemes documentation](https://picocss.com/docs/color-schemes)
- Pico CSS GitHub: [Add inline script in head to prevent FOUC · picocss/examples #18](https://github.com/picocss/examples/issues/18)
- HTMX Documentation: [hx-swap attribute](https://htmx.org/attributes/hx-swap/), [Tabs (HATEOAS) example](https://htmx.org/examples/tabs-hateoas/)
- HTMX GitHub: [Troublesome Tables · Issue #2654](https://github.com/bigskysoftware/htmx/issues/2654)
- W3C WAI: [Understanding SC 1.4.13 Content on Hover or Focus](https://www.w3.org/WAI/WCAG21/Understanding/content-on-hover-or-focus.html)
- Sarah Higley: [Tooltips in the time of WCAG 2.1](https://sarahmhigley.com/writing/tooltips-in-wcag-21/)
- Smashing Magazine: [Getting Started With The Popover API](https://www.smashingmagazine.com/2026/03/getting-started-popover-api/)
- Frontend Masters Blog: [Using the Popover API for HTML Tooltips](https://frontendmasters.com/blog/using-the-popover-api-for-html-tooltips/)
- n8d.at: [Why input[type="number"] Hurts Your User Experience](https://n8d.at/inputtypenumber-and-why-it-isnt-good-for-your-user-experience/)
- Sean McP: [Be careful parsing formatted numbers in JavaScript](https://www.seanmcp.com/articles/be-careful-parsing-formatted-numbers-in-javascript/)
- Cassidy James Blaede: [Give your SVGs light/dark style support](https://cassidyjames.com/blog/prefers-color-scheme-svg-light-dark/)
- Jonathan Harrell: [Dynamic SVGs in Light & Dark Mode](https://www.jonathanharrell.com/blog/light-dark-mode-svgs)
- Flask Security Docs: [Security Considerations](https://flask.palletsprojects.com/en/stable/web-security/)
- Werkzeug GitHub: [send_file Content-Disposition filename issues #2529](https://github.com/pallets/werkzeug/issues/2529)
- Josh Comeau: [What The Heck, z-index? — Stacking Contexts](https://www.joshwcomeau.com/css/stacking-contexts/)

---
*Pitfalls research for: Fathom v1.1 — tooltips, breakdown table, JSON export/import, comma inputs, dark mode*
*Researched: 2026-03-13*
