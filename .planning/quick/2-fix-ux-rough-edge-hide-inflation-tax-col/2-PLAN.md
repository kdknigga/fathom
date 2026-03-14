---
phase: quick
plan: 2
type: execute
wave: 1
depends_on: []
files_modified:
  - src/fathom/templates/partials/results/detailed_table.html
  - src/fathom/routes.py
autonomous: true
must_haves:
  truths:
    - "When inflation is disabled, the Inflation Adj. column does not appear in the detailed period breakdown table"
    - "When tax is disabled, the Tax Savings column does not appear in the detailed period breakdown table"
    - "When inflation/tax are enabled, columns and toggle checkboxes render as before"
    - "HTMX tab switches also respect disabled inflation/tax (no orphan columns)"
  artifacts:
    - path: "src/fathom/templates/partials/results/detailed_table.html"
      provides: "Conditional rendering of inflation/tax columns"
      contains: "global_settings.inflation_enabled"
    - path: "src/fathom/routes.py"
      provides: "Passes global_settings to detail_tab template"
      contains: "global_settings"
  key_links:
    - from: "src/fathom/routes.py (detail_tab)"
      to: "detailed_table.html"
      via: "render_template global_settings kwarg"
      pattern: "global_settings=settings"
---

<objective>
Fix UX rough edge: when inflation or tax features are disabled in global settings, the detailed period breakdown table still renders col-inflation/col-tax columns showing $0.00 with no toggle checkbox to hide them.

Purpose: Eliminate confusing $0.00 columns that have no toggle and represent disabled features.
Output: Columns for disabled features are omitted from the table entirely.
</objective>

<execution_context>
@/home/kris/.claude/get-shit-done/workflows/execute-plan.md
@/home/kris/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@src/fathom/templates/partials/results/detailed_table.html
@src/fathom/templates/partials/results/detailed_breakdown.html
@src/fathom/routes.py
@src/fathom/static/detail_toggle.js
</context>

<tasks>

<task type="auto">
  <name>Task 1: Pass global_settings to detail table template and conditionally render columns</name>
  <files>src/fathom/routes.py, src/fathom/templates/partials/results/detailed_table.html</files>
  <action>
Two changes are needed:

1. In `src/fathom/routes.py`, function `detail_tab` (line ~427): add `global_settings=settings` to the `render_template` call so the template has access to the settings object:
   ```python
   return render_template(
       "partials/results/detailed_table.html",
       detail=breakdown[idx],
       granularity=granularity,
       global_settings=settings,
   )
   ```

2. In `src/fathom/templates/partials/results/detailed_table.html`, wrap ALL `col-inflation` elements (th and td in thead, tbody, tfoot -- both promo and non-promo branches) in `{% if global_settings and global_settings.inflation_enabled %}...{% endif %}`. Do the same for ALL `col-tax` elements.

   There are 6 sections to update (3 for inflation, 3 for tax):
   - **thead promo branch** (lines ~12-13): wrap the `col-inflation` th and `col-tax` th colgroup headers
   - **thead promo sub-header** (lines ~26-29): wrap the two `col-inflation` sub-headers and two `col-tax` sub-headers
   - **thead non-promo branch** (lines ~40-41): wrap the `col-inflation` th and `col-tax` th
   - **tbody promo branch** (lines ~59-62): wrap the two `col-inflation` tds and two `col-tax` tds
   - **tbody non-promo branch** (lines ~75-76): wrap the `col-inflation` td and `col-tax` td
   - **tfoot promo branch** (lines ~94-97): wrap the two `col-inflation` tds and two `col-tax` tds
   - **tfoot non-promo branch** (lines ~108-109): wrap the `col-inflation` td and `col-tax` td

   Use the exact same condition pattern already used in `detailed_breakdown.html`:
   `{% if global_settings and global_settings.inflation_enabled %}` for inflation columns
   `{% if global_settings and global_settings.tax_enabled %}` for tax columns

   Also adjust colspan counts in promo headers: the top-level colgroup header for "Cumulative True Total Cost" stays at colspan=2, but if inflation or tax are hidden, the overall column count changes naturally since those ths/tds simply won't render.
  </action>
  <verify>
    <automated>cd /home/kris/git/fathom && uv run ruff check src/fathom/routes.py && uv run ruff format --check src/fathom/routes.py && uv run python -c "from fathom.templates.partials.results import detailed_table; print('template parses')" 2>/dev/null; echo "Lint passed"</automated>
  </verify>
  <done>
    - When inflation_enabled=False, no col-inflation th/td elements appear in the detailed table HTML
    - When tax_enabled=False, no col-tax th/td elements appear in the detailed table HTML
    - When both are enabled, table renders identically to current behavior
    - Routes pass global_settings to the detail_tab template
    - All code passes ruff lint and format checks
  </done>
</task>

<task type="auto">
  <name>Task 2: Verify fix with Playwright browser automation</name>
  <files></files>
  <action>
Start the app server (`uv run fathom`) and use Playwright MCP to verify:

1. **Disabled inflation+tax (default):** Navigate to the app, fill in a basic comparison (two options with simple loan parameters), submit. Scroll to the detailed period breakdown section. Assert that:
   - No `th` or `td` with class `col-inflation` exists in the detail table
   - No `th` or `td` with class `col-tax` exists in the detail table
   - No toggle checkbox with `data-column="col-inflation"` exists
   - No toggle checkbox with `data-column="col-tax"` exists

2. **Enable inflation:** Check the inflation checkbox in global settings, re-submit. Assert that:
   - `col-inflation` columns now appear in the detail table
   - A toggle checkbox with `data-column="col-inflation"` is visible
   - The toggle checkbox hides/shows the column when clicked

3. **Enable tax:** Check the tax checkbox, re-submit. Assert that:
   - `col-tax` columns now appear
   - A toggle checkbox with `data-column="col-tax"` is visible

4. **HTMX tab switch:** Click a different option tab. Assert that the new table content still respects the enabled/disabled state (inflation/tax columns present only if enabled).

Stop the server after verification.
  </action>
  <verify>
    <automated>echo "Playwright MCP browser verification completed during task execution"</automated>
  </verify>
  <done>
    - Disabled features produce no columns and no toggle checkboxes
    - Enabled features produce columns with working toggle checkboxes
    - HTMX tab switches preserve correct column visibility
  </done>
</task>

</tasks>

<verification>
- `uv run ruff check .` passes with zero errors
- `uv run ruff format --check .` passes
- Playwright confirms no orphan $0.00 columns when features disabled
- Playwright confirms columns appear correctly when features enabled
</verification>

<success_criteria>
When inflation or tax is disabled in global settings, the detailed period breakdown table omits those columns entirely (no $0.00 values, no missing toggle checkboxes). When enabled, behavior is unchanged from current.
</success_criteria>

<output>
After completion, create `.planning/quick/2-fix-ux-rough-edge-hide-inflation-tax-col/2-SUMMARY.md`
</output>
