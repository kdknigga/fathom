"""
Playwright browser verification for HTMX, charts, and accessibility.

Automated browser-based checks per plan 03-03 Task 3.
This script is NOT a pytest test -- it runs standalone via Playwright.
"""

import sys
import tempfile
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE_URL = "http://localhost:5001"
PASSED: list[str] = []
FAILED: list[str] = []

# Use a dedicated temp directory for screenshots
_SCREENSHOT_DIR = Path(tempfile.mkdtemp(prefix="fathom-screenshots-"))


def check(name, condition, detail=""):
    """Record a check result."""
    if condition:
        PASSED.append(name)
        print(f"  PASS: {name}")
    else:
        FAILED.append(name)
        print(f"  FAIL: {name} -- {detail}")


def _parse_color_component(color_str):
    """Extract RGB values from a computed color string like 'rgb(r, g, b)'."""
    import re

    match = re.search(r"rgb\((\d+),\s*(\d+),\s*(\d+)\)", color_str)
    if match:
        return int(match.group(1)), int(match.group(2)), int(match.group(3))
    return None


def _is_dark_color(r, g, b):
    """Check if an RGB color is dark (luminance < 128)."""
    luminance = 0.299 * r + 0.587 * g + 0.114 * b
    return luminance < 128


def _is_light_color(r, g, b):
    """Check if an RGB color is light (luminance >= 128)."""
    return not _is_dark_color(r, g, b)


def fill_valid_form(page):
    """Fill in valid form data: Cash vs Traditional Loan."""
    # Purchase price
    page.fill("#purchase-price", "25000")

    # Option 0 is already Cash by default, set label
    page.fill('input[name="options[0][label]"]', "Pay in Full")

    # Option 1 is already Traditional Loan by default
    page.fill('input[name="options[1][label]"]', "Bank Loan")
    page.fill('input[name="options[1][apr]"]', "6")
    page.fill('input[name="options[1][term_months]"]', "36")
    page.fill('input[name="options[1][down_payment]"]', "5000")


def verify_dark_mode(browser):
    """Verify dark mode rendering of charts and page elements."""
    print("\n--- Check 8: Dark mode verification ---")
    context = browser.new_context(
        viewport={"width": 1280, "height": 720},
        color_scheme="dark",
    )
    page = context.new_page()

    # Navigate and immediately check background is dark (no flash)
    page.goto(BASE_URL)
    bg_color = page.evaluate(
        "() => getComputedStyle(document.documentElement).backgroundColor",
    )
    bg_rgb = _parse_color_component(bg_color)
    check(
        "Dark mode: page background is dark",
        bg_rgb is not None and _is_dark_color(*bg_rgb),
        f"Background color: {bg_color}",
    )

    # Fill form and submit to get results
    fill_valid_form(page)
    page.click("#compare-btn")
    page.wait_for_selector("#results .recommendation-card", timeout=10000)

    shot_path = str(_SCREENSHOT_DIR / "dark-mode-results.png")
    page.screenshot(path=shot_path, full_page=True)
    print(f"  Screenshot: {shot_path}")

    # Check caveat card visibility (if caveats exist)
    caveats = page.query_selector_all(".caveat")
    if caveats:
        caveat_bg = page.evaluate(
            "() => getComputedStyle(document.querySelector('.caveat')).backgroundColor",
        )
        caveat_rgb = _parse_color_component(caveat_bg)
        check(
            "Dark mode: caveat card has dark background",
            caveat_rgb is not None and _is_dark_color(*caveat_rgb),
            f"Caveat bg: {caveat_bg}",
        )

    # Check SVG chart text legibility (bar chart labels should be light)
    bar_label_fills = page.evaluate("""() => {
        const texts = document.querySelectorAll('.chart-bar text');
        return Array.from(texts).map(t => getComputedStyle(t).fill);
    }""")
    if bar_label_fills:
        light_count = 0
        for fill_str in bar_label_fills:
            rgb = _parse_color_component(fill_str)
            if rgb and _is_light_color(*rgb):
                light_count += 1
        check(
            "Dark mode: bar chart text is legible (light fill)",
            light_count > 0,
            f"Light fills: {light_count}/{len(bar_label_fills)}",
        )

    # Check line chart text legibility
    line_label_fills = page.evaluate("""() => {
        const texts = document.querySelectorAll('.chart-line text');
        return Array.from(texts).map(t => getComputedStyle(t).fill);
    }""")
    if line_label_fills:
        light_count = 0
        for fill_str in line_label_fills:
            rgb = _parse_color_component(fill_str)
            if rgb and _is_light_color(*rgb):
                light_count += 1
        check(
            "Dark mode: line chart text is legible (light fill)",
            light_count > 0,
            f"Light fills: {light_count}/{len(line_label_fills)}",
        )

    # Check pattern backgrounds are not white (skip solid pattern which uses currentColor)
    pattern_fills = page.evaluate("""() => {
        const patterns = document.querySelectorAll('pattern:not(#bar-pattern-solid) rect');
        return Array.from(patterns).map(r => getComputedStyle(r).fill);
    }""")
    if pattern_fills:
        white_count = 0
        for fill_str in pattern_fills:
            rgb = _parse_color_component(fill_str)
            if rgb and rgb[0] > 240 and rgb[1] > 240 and rgb[2] > 240:
                white_count += 1
        check(
            "Dark mode: pattern backgrounds not white",
            white_count == 0,
            f"White patterns: {white_count}/{len(pattern_fills)}",
        )

    # Check winner column highlight visibility
    winner_cols = page.query_selector_all(".winner-col")
    if winner_cols:
        winner_bg = page.evaluate(
            "() => getComputedStyle(document.querySelector('.winner-col')).backgroundColor",
        )
        check(
            "Dark mode: winner column has visible background",
            winner_bg not in {"rgba(0, 0, 0, 0)", "transparent"},
            f"Winner col bg: {winner_bg}",
        )

    context.close()


def verify_comma_formatting(browser):
    """Verify client-side comma formatting on monetary input fields."""
    print("\n--- Check 10: Comma formatting - blur adds commas ---")
    context = browser.new_context(viewport={"width": 1280, "height": 720})
    page = context.new_page()
    page.goto(BASE_URL)

    # Test 1: Blur formatting - type raw number, blur, see commas
    price_field = page.locator("#purchase-price")
    price_field.click()
    price_field.fill("100000")
    # Click elsewhere to trigger blur
    page.locator("h1").click()
    page.wait_for_timeout(200)
    val = price_field.input_value()
    check(
        "Comma: blur formats 100000 as 100,000",
        val == "100,000",
        f"Got: {val}",
    )

    # Test 2: Focus stripping - click back in, commas removed
    print("\n--- Check 11: Comma formatting - focus strips commas ---")
    price_field.click()
    page.wait_for_timeout(100)
    val = price_field.input_value()
    check(
        "Comma: focus strips 100,000 to 100000",
        val == "100000",
        f"Got: {val}",
    )

    # Test 3: Decimal preservation on blur
    print("\n--- Check 12: Comma formatting - decimal preservation ---")
    price_field.fill("25000.50")
    page.locator("h1").click()
    page.wait_for_timeout(200)
    val = price_field.input_value()
    check(
        "Comma: blur preserves decimals 25000.50 -> 25,000.50",
        val == "25,000.50",
        f"Got: {val}",
    )

    # Test 4: Paste cleaning
    print("\n--- Check 13: Comma formatting - paste cleans input ---")
    price_field.click()
    price_field.fill("")
    # Simulate paste via JS dispatch
    page.evaluate("""() => {
        const field = document.getElementById('purchase-price');
        field.focus();
        const pasteEvent = new ClipboardEvent('paste', {
            bubbles: true,
            cancelable: true,
            clipboardData: new DataTransfer()
        });
        pasteEvent.clipboardData.setData('text', '$100,000');
        field.dispatchEvent(pasteEvent);
    }""")
    page.wait_for_timeout(200)
    val = price_field.input_value()
    check(
        "Comma: paste cleans '$100,000' to '100000'",
        val == "100000",
        f"Got: {val}",
    )

    # Test 5: Server-rendered comma values after submit
    print("\n--- Check 14: Comma formatting - server renders commas ---")
    page.goto(BASE_URL)
    fill_valid_form(page)
    page.click("#compare-btn")
    page.wait_for_selector("#results .recommendation-card", timeout=10000)
    # After HTMX swap, check purchase price field still has comma-formatted value
    price_val = price_field.input_value()
    check(
        "Comma: server renders purchase_price with commas (25,000)",
        price_val == "25,000",
        f"Got: {price_val}",
    )

    # Test 6: HTMX swap preserves formatting on new fields
    print("\n--- Check 15: Comma formatting - HTMX swap new fields ---")
    page.goto(BASE_URL)
    # Option 1 is Traditional Loan by default - change to Promo (0% APR)
    option1_type = page.locator("#option-1-type")
    option1_type.select_option("promo_zero_percent")
    # Wait for HTMX swap of option fields
    page.wait_for_selector(
        '#option-1-fields input[name="options[1][down_payment]"]',
        timeout=5000,
    )
    # Type in the new down_payment field and blur
    dp_field = page.locator('input[name="options[1][down_payment]"]')
    dp_field.click()
    dp_field.fill("15000")
    page.locator("h1").click()
    page.wait_for_timeout(200)
    dp_val = dp_field.input_value()
    check(
        "Comma: HTMX-swapped field formats 15000 as 15,000",
        dp_val == "15,000",
        f"Got: {dp_val}",
    )

    # Test 7: Full calculation with comma-containing input
    print("\n--- Check 16: Comma formatting - full calc with commas ---")
    page.goto(BASE_URL)
    price_field = page.locator("#purchase-price")
    price_field.click()
    price_field.fill("100000")
    # Blur to add commas
    page.locator("h1").click()
    page.wait_for_timeout(200)

    # Fill option labels
    page.fill('input[name="options[0][label]"]', "Pay Cash")
    page.fill('input[name="options[1][label]"]', "Bank Loan")
    page.fill('input[name="options[1][apr]"]', "6")
    page.fill('input[name="options[1][term_months]"]', "36")
    page.fill('input[name="options[1][down_payment]"]', "10000")

    page.click("#compare-btn")
    page.wait_for_selector("#results .recommendation-card", timeout=10000)
    card_text = page.inner_text(".recommendation-card")
    check(
        "Comma: full calc succeeds with comma input (recommendation visible)",
        "Saves" in card_text or "savings" in card_text.lower(),
        f"Card text: {card_text[:200]}",
    )

    shot_path = str(_SCREENSHOT_DIR / "comma-formatting.png")
    page.screenshot(path=shot_path, full_page=True)
    print(f"  Screenshot: {shot_path}")

    context.close()


def verify_light_mode(browser):
    """Verify light mode rendering still works correctly."""
    print("\n--- Check 9: Light mode verification ---")
    context = browser.new_context(
        viewport={"width": 1280, "height": 720},
        color_scheme="light",
    )
    page = context.new_page()

    page.goto(BASE_URL)
    bg_color = page.evaluate(
        "() => getComputedStyle(document.documentElement).backgroundColor",
    )
    bg_rgb = _parse_color_component(bg_color)
    check(
        "Light mode: page background is light",
        bg_rgb is not None and _is_light_color(*bg_rgb),
        f"Background color: {bg_color}",
    )

    # Fill form and submit
    fill_valid_form(page)
    page.click("#compare-btn")
    page.wait_for_selector("#results .recommendation-card", timeout=10000)

    shot_path = str(_SCREENSHOT_DIR / "light-mode-results.png")
    page.screenshot(path=shot_path, full_page=True)
    print(f"  Screenshot: {shot_path}")

    # Check bar chart text is visible (dark fill on light bg)
    bar_label_fills = page.evaluate("""() => {
        const texts = document.querySelectorAll('.chart-bar text');
        return Array.from(texts).map(t => getComputedStyle(t).fill);
    }""")
    if bar_label_fills:
        has_dark = any(
            _is_dark_color(*rgb)
            for fill_str in bar_label_fills
            if (rgb := _parse_color_component(fill_str))
        )
        check(
            "Light mode: bar chart text has dark fills",
            has_dark,
            f"Fills: {bar_label_fills[:3]}",
        )

    # Check pattern backgrounds are white/light (skip solid which uses currentColor)
    pattern_fills = page.evaluate("""() => {
        const patterns = document.querySelectorAll('pattern:not(#bar-pattern-solid) rect');
        return Array.from(patterns).map(r => getComputedStyle(r).fill);
    }""")
    if pattern_fills:
        all_light = all(
            _is_light_color(*rgb)
            for fill_str in pattern_fills
            if (rgb := _parse_color_component(fill_str))
        )
        check(
            "Light mode: pattern backgrounds are light",
            all_light,
            f"Fills: {pattern_fills[:3]}",
        )

    context.close()


def verify_export_import(browser):
    """Verify JSON export/import functionality in the browser."""
    print("\n--- Check 17: Export button exists and is styled correctly ---")
    context = browser.new_context(viewport={"width": 1280, "height": 720})
    page = context.new_page()
    page.goto(BASE_URL)

    # 1. Export button exists with correct attributes
    export_btn = page.locator('button[formaction="/export"]')
    check(
        "Export: button is visible",
        export_btn.is_visible(),
    )
    check(
        "Export: button has outline class",
        "outline" in (export_btn.get_attribute("class") or ""),
        f"Class: {export_btn.get_attribute('class')}",
    )
    check(
        "Export: button has hx-disable attribute",
        export_btn.get_attribute("hx-disable") is not None,
    )
    check(
        "Export: button has formnovalidate",
        export_btn.get_attribute("formnovalidate") is not None,
    )

    # 2. Import button/label exists
    print("\n--- Check 18: Import button exists ---")
    import_label = page.locator('label[for="import-file"]')
    check(
        "Import: label is visible",
        import_label.is_visible(),
    )
    check(
        "Import: label has role=button",
        import_label.get_attribute("role") == "button",
    )
    file_input = page.locator("#import-file")
    check(
        "Import: file input exists",
        file_input.count() == 1,
    )
    check(
        "Import: file input accepts .json",
        ".json" in (file_input.get_attribute("accept") or ""),
    )
    check(
        "Import: file input is hidden",
        file_input.get_attribute("hidden") is not None,
    )

    # 3. Export triggers a file download (not a DOM swap)
    print("\n--- Check 19: Export triggers file download ---")
    fill_valid_form(page)

    import json as _json
    import tempfile as _tempfile

    # Verify export via HTTP response inspection -- intercept the POST /export
    # response to confirm Content-Disposition attachment header and valid JSON
    export_response = {"headers": {}, "body": ""}

    def _capture_export(response):
        if "/export" in response.url:
            export_response["headers"] = response.headers
            export_response["body"] = response.body().decode("utf-8")

    page.on("response", _capture_export)
    export_btn.click()
    page.wait_for_timeout(2000)
    page.remove_listener("response", _capture_export)

    content_disp = export_response["headers"].get("content-disposition", "")
    check(
        "Export: response has Content-Disposition attachment",
        "attachment" in content_disp,
        f"Content-Disposition: {content_disp}",
    )
    check(
        "Export: filename starts with 'fathom-'",
        "fathom-" in content_disp,
        f"Content-Disposition: {content_disp}",
    )
    check(
        "Export: filename ends with '.json'",
        ".json" in content_disp,
        f"Content-Disposition: {content_disp}",
    )

    # Parse the response body as JSON
    export_content = {}
    download_path = None
    _json_errors = (ValueError, _json.JSONDecodeError)
    try:
        export_content = _json.loads(export_response["body"])
    except _json_errors:
        is_valid = False
        check(
            "Export: response is valid JSON",
            is_valid,
            "Could not parse body as JSON",
        )

    if export_content:
        check(
            "Export: JSON has version field",
            "version" in export_content,
            f"Keys: {list(export_content.keys())}",
        )
        check(
            "Export: JSON has purchase_price",
            "purchase_price" in export_content,
        )
        # The form value may include commas from client-side formatting
        pp = export_content.get("purchase_price", "")
        check(
            "Export: purchase_price is '25000' or '25,000'",
            pp in ("25000", "25,000"),
            f"Got: {pp}",
        )
        check(
            "Export: JSON has options",
            "options" in export_content and len(export_content["options"]) == 2,
            f"Options count: {len(export_content.get('options', []))}",
        )

    # Navigate back to main page for subsequent tests
    page.goto(BASE_URL)

    # 4. Import restores form values
    print("\n--- Check 20: Import restores form values ---")
    # Create a valid test JSON file for import
    test_data = {
        "version": 1,
        "purchase_price": "50000",
        "options": [
            {"type": "cash", "label": "Cash Payment"},
            {
                "type": "traditional_loan",
                "label": "Auto Loan",
                "apr": "4.5",
                "term_months": "48",
                "down_payment": "10000",
            },
        ],
        "settings": {
            "return_preset": "0.07",
            "return_rate_custom": "",
            "inflation_enabled": False,
            "inflation_rate": "3",
            "tax_enabled": False,
            "tax_rate": "22",
        },
    }
    with _tempfile.NamedTemporaryFile(suffix=".json", delete=False) as import_tmp:
        import_file_path = Path(import_tmp.name)
    import_file_path.write_text(_json.dumps(test_data))

    # Upload via file input using set_input_files
    file_input = page.locator("#import-file")
    with page.expect_navigation():
        file_input.set_input_files(str(import_file_path))
    page.wait_for_load_state("networkidle")

    # Check that imported values appear in form fields
    price_val = page.locator("#purchase-price").input_value()
    check(
        "Import: purchase price is '50,000'",
        price_val == "50,000",
        f"Got: {price_val}",
    )

    option0_label = page.locator('input[name="options[0][label]"]').input_value()
    check(
        "Import: option 0 label is 'Cash Payment'",
        option0_label == "Cash Payment",
        f"Got: {option0_label}",
    )

    option1_label = page.locator('input[name="options[1][label]"]').input_value()
    check(
        "Import: option 1 label is 'Auto Loan'",
        option1_label == "Auto Loan",
        f"Got: {option1_label}",
    )

    option1_apr = page.locator('input[name="options[1][apr]"]').input_value()
    check(
        "Import: option 1 APR is '4.5'",
        option1_apr == "4.5",
        f"Got: {option1_apr}",
    )

    option1_term = page.locator('input[name="options[1][term_months]"]').input_value()
    check(
        "Import: option 1 term is '48'",
        option1_term == "48",
        f"Got: {option1_term}",
    )

    option1_dp = page.locator('input[name="options[1][down_payment]"]').input_value()
    check(
        "Import: option 1 down payment is '10,000'",
        option1_dp == "10,000",
        f"Got: {option1_dp}",
    )

    # Check no error messages shown
    error_elements = page.locator(".field-error")
    check(
        "Import: no error messages shown",
        error_elements.count() == 0,
        f"Found {error_elements.count()} errors",
    )

    # 5. Invalid import shows error
    print("\n--- Check 21: Invalid import shows error ---")
    # Navigate fresh to ensure clean state
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")

    with _tempfile.NamedTemporaryFile(suffix=".json", delete=False) as invalid_tmp:
        invalid_file_path = Path(invalid_tmp.name)
    invalid_file_path.write_text("this is not json{{{")

    file_input = page.locator("#import-file")
    # Use expect_navigation to wait for the form submission triggered by onchange
    with page.expect_navigation():
        file_input.set_input_files(str(invalid_file_path))
    page.wait_for_load_state("networkidle")

    # Check for error message (may have role="alert" or just class="field-error")
    error_msg = page.locator(".field-error")
    error_count = error_msg.count()
    check(
        "Import: error message displayed for invalid JSON",
        error_count > 0,
        "No error message found",
    )
    if error_count > 0:
        error_text = error_msg.first.inner_text()
        check(
            "Import: error mentions 'not a valid Fathom export'",
            "not a valid" in error_text.lower() or "fathom" in error_text.lower(),
            f"Error text: {error_text}",
        )

    shot_path = str(_SCREENSHOT_DIR / "import-error.png")
    page.screenshot(path=shot_path, full_page=True)
    print(f"  Screenshot: {shot_path}")

    # 6. Accessibility: keyboard focus
    print("\n--- Check 22: Export/Import keyboard accessibility ---")
    page.goto(BASE_URL)
    export_btn = page.locator('button[formaction="/export"]')
    check(
        "Export: button is keyboard-focusable (tabindex not -1)",
        export_btn.get_attribute("tabindex") != "-1",
    )

    import_label = page.locator('label[for="import-file"]')
    check(
        "Import: label has role=button for accessibility",
        import_label.get_attribute("role") == "button",
    )

    # Clean up temp files
    if download_path:
        download_path.unlink(missing_ok=True)
    import_file_path.unlink(missing_ok=True)
    invalid_file_path.unlink(missing_ok=True)

    context.close()


def fill_form_with_settings(page):
    """Fill form with Cash vs Loan and enable opportunity cost, inflation, tax."""
    page.fill("#purchase-price", "10000")
    page.fill('input[name="options[0][label]"]', "Pay in Full")
    page.fill('input[name="options[1][label]"]', "Traditional Loan")
    page.fill('input[name="options[1][apr]"]', "6")
    page.fill('input[name="options[1][term_months]"]', "36")
    page.fill('input[name="options[1][down_payment]"]', "0")

    # Open Global Settings and enable opportunity cost (7% moderate is default)
    page.locator("summary:text('Global Settings')").click()
    page.wait_for_timeout(200)

    # Select 7% moderate return rate (should already be selected but be explicit)
    page.locator('input[name="return_preset"][value="0.07"]').check()

    # Enable inflation
    page.locator('input[name="inflation_enabled"]').check()
    page.fill('input[name="inflation_rate"]', "3")

    # Enable tax
    page.locator('input[name="tax_enabled"]').check()
    page.fill('input[name="tax_rate"]', "22")


def verify_detailed_breakdown(browser):
    """Verify detailed period breakdown: tabs, toggles, compare, a11y, granularity."""
    context = browser.new_context(viewport={"width": 1280, "height": 720})
    page = context.new_page()
    page.goto(BASE_URL)

    # Setup: fill form with settings enabled and submit
    fill_form_with_settings(page)
    page.click("#compare-btn")
    page.wait_for_selector("#results .recommendation-card", timeout=10000)

    # === DETAIL-01: Per-period data renders ===
    print("\n--- Check 23: DETAIL-01 -- Per-period data renders ---")

    # Scroll to detailed breakdown section
    detail_section = page.locator(".detail-tabs")
    detail_section.scroll_into_view_if_needed()
    page.wait_for_timeout(500)

    # Verify table exists with expected column headers
    detail_table = page.locator(".detail-table")
    check(
        "Detail: table exists",
        detail_table.count() > 0,
    )

    # Check column headers (first option tab = Traditional Loan at index 1,
    # but first tab is Pay in Full at index 0)
    # Actually the first tab (Pay in Full / Cash) is loaded by default
    headers = page.locator(".detail-table thead th")
    header_texts = headers.all_text_contents()
    check(
        "Detail: Period column header exists",
        any("Period" in h for h in header_texts),
        f"Headers: {header_texts}",
    )
    check(
        "Detail: Payment column header exists",
        any("Payment" in h for h in header_texts),
        f"Headers: {header_texts}",
    )
    check(
        "Detail: Opp. Cost column header exists",
        any("Opp" in h for h in header_texts),
        f"Headers: {header_texts}",
    )
    check(
        "Detail: Cumulative True Total Cost header exists",
        any("Cumulative" in h for h in header_texts),
        f"Headers: {header_texts}",
    )

    # Click the second tab (Traditional Loan) to get a 36-month table
    loan_tab = page.locator("#detail-tab-1")
    loan_tab.click()
    page.wait_for_timeout(1000)

    # Verify the table has 36 rows (36-month loan)
    body_rows = page.locator(".detail-table tbody tr")
    row_count = body_rows.count()
    check(
        "Detail: 36 rows for 36-month loan",
        row_count == 36,
        f"Got {row_count} rows",
    )

    # Verify non-zero values in opportunity cost column
    opp_cells = page.locator(".detail-table tbody td.col-opportunity")
    if opp_cells.count() > 0:
        first_opp = opp_cells.first.inner_text()
        check(
            "Detail: Opportunity cost has non-zero values",
            first_opp != "$0.00",
            f"First opp cost: {first_opp}",
        )

    # Verify totals row (tfoot) exists
    tfoot = page.locator(".detail-table tfoot")
    check(
        "Detail: tfoot totals row exists",
        tfoot.count() > 0,
    )
    totals_text = tfoot.inner_text()
    check(
        "Detail: totals row has 'Total' label",
        "Total" in totals_text,
        f"Totals: {totals_text[:100]}",
    )

    shot_path = str(_SCREENSHOT_DIR / "detail-table.png")
    page.screenshot(path=shot_path, full_page=True)
    print(f"  Screenshot: {shot_path}")

    # === DETAIL-02: Tab switching ===
    print("\n--- Check 24: DETAIL-02 -- Tab switching ---")

    # Verify tabs exist for each option
    tab_0 = page.locator("#detail-tab-0")
    tab_1 = page.locator("#detail-tab-1")
    tab_compare = page.locator("#detail-tab-compare")
    check("Detail: tab 0 (Pay in Full) exists", tab_0.count() == 1)
    check("Detail: tab 1 (Traditional Loan) exists", tab_1.count() == 1)
    check("Detail: Compare tab exists", tab_compare.count() == 1)

    # Get content from currently active tab (Traditional Loan, tab 1)
    current_content = page.locator("#detail-panel").inner_html()

    # Click first tab (Pay in Full)
    tab_0.click()
    page.wait_for_timeout(1000)

    new_content = page.locator("#detail-panel").inner_html()
    check(
        "Detail: tab switch changes table content",
        new_content != current_content,
        "Content did not change on tab switch",
    )

    # Verify aria-selected states
    check(
        "Detail: clicked tab has aria-selected=true",
        tab_0.get_attribute("aria-selected") == "true",
        f"Got: {tab_0.get_attribute('aria-selected')}",
    )
    check(
        "Detail: other tab has aria-selected=false",
        tab_1.get_attribute("aria-selected") == "false",
        f"Got: {tab_1.get_attribute('aria-selected')}",
    )

    # === DETAIL-03: Compare tab ===
    print("\n--- Check 25: DETAIL-03 -- Compare tab ---")

    tab_compare.click()
    page.wait_for_timeout(1000)

    # Verify compare table has columns for each option
    compare_headers = page.locator(".detail-table thead th")
    compare_header_texts = compare_headers.all_text_contents()
    check(
        "Detail: Compare shows 'Pay in Full' column group",
        any("Pay in Full" in h for h in compare_header_texts),
        f"Headers: {compare_header_texts}",
    )
    check(
        "Detail: Compare shows 'Traditional Loan' column group",
        any("Traditional Loan" in h for h in compare_header_texts),
        f"Headers: {compare_header_texts}",
    )
    check(
        "Detail: Compare shows 'Payment' sub-headers",
        compare_header_texts.count("Payment") >= 2,
        f"Headers: {compare_header_texts}",
    )
    check(
        "Detail: Compare shows 'Cumulative' sub-headers",
        compare_header_texts.count("Cumulative") >= 2,
        f"Headers: {compare_header_texts}",
    )

    # Verify same number of period rows as option tab
    compare_rows = page.locator(".detail-table tbody tr")
    compare_row_count = compare_rows.count()
    check(
        "Detail: Compare has 36 period rows",
        compare_row_count == 36,
        f"Got {compare_row_count} rows",
    )

    # Verify compare tab aria state
    check(
        "Detail: Compare tab has aria-selected=true",
        tab_compare.get_attribute("aria-selected") == "true",
    )

    shot_path = str(_SCREENSHOT_DIR / "detail-compare.png")
    page.screenshot(path=shot_path, full_page=True)
    print(f"  Screenshot: {shot_path}")

    # === DETAIL-04: Column toggles ===
    print("\n--- Check 26: DETAIL-04 -- Column toggles ---")

    # Switch back to an option tab first (toggles apply to option tabs)
    tab_1.click()
    page.wait_for_timeout(1000)

    # Uncheck the Interest checkbox
    interest_toggle = page.locator('.col-toggle[data-column="col-interest"]')
    interest_toggle.uncheck()
    page.wait_for_timeout(300)

    # Verify interest cells are hidden
    interest_cells = page.locator(".detail-table .col-interest")
    if interest_cells.count() > 0:
        first_interest_display = interest_cells.first.evaluate(
            "el => getComputedStyle(el).display",
        )
        check(
            "Detail: Interest column hidden after uncheck",
            first_interest_display == "none",
            f"Display: {first_interest_display}",
        )

    # Switch to another tab and verify persistence
    tab_0.click()
    page.wait_for_timeout(1000)

    interest_cells_tab0 = page.locator(".detail-table .col-interest")
    if interest_cells_tab0.count() > 0:
        persisted_display = interest_cells_tab0.first.evaluate(
            "el => getComputedStyle(el).display",
        )
        check(
            "Detail: Interest column still hidden after tab switch (persists)",
            persisted_display == "none",
            f"Display: {persisted_display}",
        )

    # Re-check the Interest checkbox
    interest_toggle.check()
    page.wait_for_timeout(300)

    # Verify the column reappears
    interest_cells_after = page.locator(".detail-table .col-interest")
    if interest_cells_after.count() > 0:
        reappear_display = interest_cells_after.first.evaluate(
            "el => getComputedStyle(el).display",
        )
        check(
            "Detail: Interest column reappears after re-check",
            reappear_display != "none",
            f"Display: {reappear_display}",
        )

    # === DETAIL-05: Accessibility ===
    print("\n--- Check 27: DETAIL-05 -- Accessibility ---")

    # Verify tablist role
    tablist = page.locator('.detail-tabs[role="tablist"]')
    check(
        "Detail: tab container has role=tablist",
        tablist.count() == 1,
    )

    # Verify each tab button has role=tab
    tab_buttons = page.locator('.detail-tabs [role="tab"]')
    tab_count = tab_buttons.count()
    check(
        "Detail: tab buttons have role=tab (>= 3)",
        tab_count >= 3,
        f"Found {tab_count}",
    )

    # Verify panel has role=tabpanel
    panel = page.locator('#detail-panel[role="tabpanel"]')
    check(
        "Detail: panel has role=tabpanel",
        panel.count() == 1,
    )

    # Verify th elements have scope=col
    th_with_scope = page.locator(".detail-table thead th[scope]")
    check(
        "Detail: th elements have scope attribute",
        th_with_scope.count() > 0,
        f"Found {th_with_scope.count()} th with scope",
    )

    # Keyboard navigation: Tab to first tab button, press Right arrow
    tab_0.focus()
    page.wait_for_timeout(100)
    page.keyboard.press("ArrowRight")
    page.wait_for_timeout(200)

    # Verify focus moved to next tab
    focused_id = page.evaluate("() => document.activeElement?.id")
    check(
        "Detail: ArrowRight moves focus to next tab",
        focused_id == "detail-tab-1",
        f"Focused: {focused_id}",
    )

    # Press Enter on focused tab to activate it
    page.keyboard.press("Enter")
    page.wait_for_timeout(1000)

    # Verify it became selected
    check(
        "Detail: Enter activates focused tab (aria-selected=true)",
        tab_1.get_attribute("aria-selected") == "true",
        f"Got: {tab_1.get_attribute('aria-selected')}",
    )

    # === Granularity toggle ===
    print("\n--- Check 28: Granularity toggle ---")

    # Record current row count (should be 36 monthly rows)
    monthly_rows = page.locator(".detail-table tbody tr").count()

    # Switch to annual view
    annual_radio = page.locator('input[name="detail-granularity"][value="annual"]')
    annual_radio.check()
    page.wait_for_timeout(1500)

    annual_rows = page.locator(".detail-table tbody tr").count()
    check(
        "Detail: Annual view has fewer rows than monthly",
        annual_rows < monthly_rows,
        f"Monthly: {monthly_rows}, Annual: {annual_rows}",
    )
    check(
        "Detail: Annual view has ~3 rows for 36-month loan",
        annual_rows == 3,
        f"Got {annual_rows} rows",
    )

    # Verify period labels show "Year X"
    first_period = page.locator(".detail-table tbody tr:first-child td:first-child")
    first_period_text = first_period.inner_text()
    check(
        "Detail: Annual period labels show 'Year 1'",
        "Year 1" in first_period_text,
        f"Got: {first_period_text}",
    )

    # Switch back to monthly
    monthly_radio = page.locator('input[name="detail-granularity"][value="monthly"]')
    monthly_radio.check()
    page.wait_for_timeout(1500)

    restored_rows = page.locator(".detail-table tbody tr").count()
    check(
        "Detail: Monthly view restores original row count",
        restored_rows == monthly_rows,
        f"Monthly: {monthly_rows}, Restored: {restored_rows}",
    )

    # === Sticky totals visual check ===
    print("\n--- Check 29: Sticky totals ---")

    # Scroll to middle of the table to check if totals remain visible
    table_scroll = page.locator(".detail-table-scroll")
    if table_scroll.count() > 0:
        # Scroll within the container
        table_scroll.evaluate("el => el.scrollTop = el.scrollHeight / 2")
        page.wait_for_timeout(300)

        shot_path = str(_SCREENSHOT_DIR / "detail-sticky-totals.png")
        page.screenshot(path=shot_path, full_page=True)
        print(f"  Screenshot: {shot_path}")

        # Verify tfoot is still in the viewport (or at least exists)
        tfoot_visible = page.locator(".detail-table tfoot .detail-totals")
        check(
            "Detail: Sticky totals row exists while scrolled",
            tfoot_visible.count() > 0,
        )

    context.close()


def main():
    """Run all Playwright browser checks."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 720})
        page = context.new_page()

        # === CHECK 1: HTMX partial swap verification ===
        print("\n--- Check 1: HTMX partial swap ---")
        page.goto(BASE_URL)
        fill_valid_form(page)

        # Get initial results content
        initial_content = page.inner_html("#results")

        # Click Compare Options
        page.click("#compare-btn")
        # Wait for HTMX swap to complete
        page.wait_for_selector("#results .recommendation-card", timeout=10000)

        # Verify results changed
        new_content = page.inner_html("#results")
        check(
            "HTMX swap updated #results",
            new_content != initial_content,
            "Content did not change",
        )
        check(
            "No DOCTYPE in partial",
            "<!DOCTYPE" not in new_content,
            "Partial contains DOCTYPE",
        )
        check(
            "Recommendation card visible",
            page.is_visible(".recommendation-card"),
        )
        # URL should NOT have changed to /compare (HTMX stays on same page)
        check(
            "URL unchanged (no full redirect)",
            page.url.rstrip("/") == BASE_URL.rstrip("/"),
            f"URL was {page.url}",
        )

        shot_path = str(_SCREENSHOT_DIR / "htmx-results.png")
        page.screenshot(path=shot_path)
        print(f"  Screenshot: {shot_path}")

        # === CHECK 2: Hero card and recommendation display ===
        print("\n--- Check 2: Hero card and recommendation ---")
        check(
            "Winner name displayed",
            page.is_visible(".recommendation-card .winner-name")
            or page.inner_text(".recommendation-card") != "",
        )
        card_text = page.inner_text(".recommendation-card")
        check(
            "Savings amount displayed",
            "$" in card_text
            and ("Saves" in card_text or "savings" in card_text.lower()),
            f"Card text: {card_text[:200]}",
        )
        page.locator(".recommendation-card").scroll_into_view_if_needed()
        shot_path = str(_SCREENSHOT_DIR / "hero-card.png")
        page.screenshot(path=shot_path, full_page=True)
        print(f"  Screenshot: {shot_path}")

        # === CHECK 3: Chart SVG rendering ===
        print("\n--- Check 3: Chart SVG rendering ---")
        bar_svg = page.query_selector('svg[aria-labelledby*="bar-chart-title"]')
        check("Bar chart SVG present", bar_svg is not None)
        if bar_svg:
            bar_html = bar_svg.inner_html()
            check("Bar chart has <pattern> elements", "<pattern" in bar_html)
            check("Bar chart has <rect> elements", "<rect" in bar_html)

        line_svg = page.query_selector('svg[aria-labelledby*="line-chart-title"]')
        check("Line chart SVG present", line_svg is not None)
        if line_svg:
            line_html = line_svg.inner_html()
            check("Line chart has <path> elements", "<path" in line_html)
            check(
                "Line chart has stroke-dasharray",
                "stroke-dasharray" in line_html,
            )

        shot_path = str(_SCREENSHOT_DIR / "charts.png")
        page.screenshot(path=shot_path)
        print(f"  Screenshot: {shot_path}")

        # === CHECK 4: Chart accessibility ===
        print("\n--- Check 4: Chart accessibility ---")
        bar_title = page.query_selector("#bar-chart-title")
        bar_desc = page.query_selector("#bar-chart-desc")
        check("Bar chart <title> exists", bar_title is not None)
        check(
            "Bar chart <title> non-empty",
            bar_title is not None and (bar_title.text_content() or "").strip() != "",
        )
        check("Bar chart <desc> exists", bar_desc is not None)

        line_title = page.query_selector("#line-chart-title")
        line_desc = page.query_selector("#line-chart-desc")
        check("Line chart <title> exists", line_title is not None)
        check("Line chart <desc> exists", line_desc is not None)

        hidden_tables = page.query_selector_all(".visually-hidden table")
        check(
            "Hidden data tables exist (>=2)",
            len(hidden_tables) >= 2,
            f"Found {len(hidden_tables)}",
        )
        if hidden_tables:
            captions = page.query_selector_all(".visually-hidden table caption")
            check(
                "Hidden tables have captions",
                len(captions) >= 2,
                f"Found {len(captions)} captions",
            )

        # === CHECK 5: Bar chart data table cell values (A11Y-02) ===
        print("\n--- Check 5: Bar chart data table cell values ---")
        bar_table = page.query_selector(
            ".visually-hidden table:has(caption:text('True Total Cost'))",
        )
        check("Bar chart data table found", bar_table is not None)
        if bar_table:
            # Verify parent div has visually-hidden class
            bar_parent = bar_table.evaluate(
                "el => el.parentElement.classList.contains('visually-hidden')",
            )
            check("Bar table parent has visually-hidden class", bar_parent)

            # Verify caption
            bar_caption = bar_table.query_selector("caption")
            check(
                "Bar table caption is 'True Total Cost comparison data'",
                bar_caption is not None
                and bar_caption.text_content().strip()
                == "True Total Cost comparison data",
                f"Got: {bar_caption.text_content().strip() if bar_caption else 'None'}",
            )

            # Verify header columns
            bar_headers = bar_table.query_selector_all("thead th")
            check(
                "Bar table has 2 header columns",
                len(bar_headers) == 2,
                f"Found {len(bar_headers)}",
            )
            if len(bar_headers) == 2:
                check(
                    "Bar table header 1 is 'Option'",
                    bar_headers[0].text_content().strip() == "Option",
                )
                check(
                    "Bar table header 2 is 'True Total Cost'",
                    bar_headers[1].text_content().strip() == "True Total Cost",
                )

            # Verify row values (known scenario: Bank Loan wins)
            bar_rows = bar_table.query_selector_all("tbody tr")
            check(
                "Bar table has 2 data rows",
                len(bar_rows) == 2,
                f"Found {len(bar_rows)}",
            )
            if len(bar_rows) >= 2:
                # Row 1: Bank Loan (Winner)
                row1_cells = bar_rows[0].query_selector_all("td")
                row1_name = row1_cells[0].text_content().strip()
                row1_cost = row1_cells[1].text_content().strip()
                check(
                    "Bar row 1: Bank Loan (Winner)",
                    "Bank Loan" in row1_name and "Winner" in row1_name,
                    f"Got: {row1_name}",
                )
                check(
                    "Bar row 1 cost: $29,171",
                    row1_cost == "$29,171",
                    f"Got: {row1_cost}",
                )

                # Row 2: Pay in Full
                row2_cells = bar_rows[1].query_selector_all("td")
                row2_name = row2_cells[0].text_content().strip()
                row2_cost = row2_cells[1].text_content().strip()
                check(
                    "Bar row 2: Pay in Full",
                    row2_name == "Pay in Full",
                    f"Got: {row2_name}",
                )
                check(
                    "Bar row 2 cost: $30,823",
                    row2_cost == "$30,823",
                    f"Got: {row2_cost}",
                )

        # === CHECK 6: Line chart data table cell values (A11Y-02 regression) ===
        print("\n--- Check 6: Line chart data table cell values (A11Y-02) ---")
        line_table = page.query_selector(
            ".visually-hidden table:has(caption:text('Cumulative'))",
        )
        check("Line chart data table found", line_table is not None)
        if line_table:
            # Verify parent div has visually-hidden class
            line_parent = line_table.evaluate(
                "el => el.parentElement.classList.contains('visually-hidden')",
            )
            check("Line table parent has visually-hidden class", line_parent)

            # Verify caption
            line_caption = line_table.query_selector("caption")
            check(
                "Line table caption is 'Cumulative cost over time data'",
                line_caption is not None
                and line_caption.text_content().strip()
                == "Cumulative cost over time data",
                f"Got: {line_caption.text_content().strip() if line_caption else 'None'}",
            )

            # Verify header columns (Month, Bank Loan, Pay in Full)
            line_headers = line_table.query_selector_all("thead th")
            check(
                "Line table has 3 header columns",
                len(line_headers) == 3,
                f"Found {len(line_headers)}",
            )
            if len(line_headers) == 3:
                check(
                    "Line table header 1 is 'Month'",
                    line_headers[0].text_content().strip() == "Month",
                )
                check(
                    "Line table header 2 is 'Bank Loan'",
                    line_headers[1].text_content().strip() == "Bank Loan",
                )
                check(
                    "Line table header 3 is 'Pay in Full'",
                    line_headers[2].text_content().strip() == "Pay in Full",
                )

            # Verify all row values (deterministic Decimal arithmetic)
            line_rows = line_table.query_selector_all("tbody tr")
            expected_line_data = [
                ("12", "$12,301", "$25,000"),
                ("24", "$19,603", "$25,000"),
                ("36", "$26,904", "$25,000"),
                ("36", "$26,904", "$25,000"),  # Final month row
            ]
            check(
                f"Line table has {len(expected_line_data)} data rows",
                len(line_rows) == len(expected_line_data),
                f"Found {len(line_rows)}",
            )
            for idx, (exp_month, exp_loan, exp_cash) in enumerate(expected_line_data):
                if idx >= len(line_rows):
                    break
                cells = line_rows[idx].query_selector_all("td")
                if len(cells) < 3:
                    enough_cells = len(cells) >= 3
                    check(
                        f"Line row {idx + 1} has 3 cells",
                        enough_cells,
                        f"Found {len(cells)}",
                    )
                    continue
                month = cells[0].text_content().strip()
                loan_val = cells[1].text_content().strip()
                cash_val = cells[2].text_content().strip()
                check(
                    f"Line row {idx + 1} month={exp_month}",
                    month == exp_month,
                    f"Got: {month}",
                )
                check(
                    f"Line row {idx + 1} Bank Loan={exp_loan}",
                    loan_val == exp_loan,
                    f"Got: {loan_val}",
                )
                check(
                    f"Line row {idx + 1} Pay in Full={exp_cash}",
                    cash_val == exp_cash,
                    f"Got: {cash_val}",
                )

        # === CHECK 7: Responsive layout at 375px ===
        print("\n--- Check 7: Responsive layout (375px) ---")
        page.set_viewport_size({"width": 375, "height": 812})
        page.goto(BASE_URL)
        fill_valid_form(page)
        page.click("#compare-btn")
        page.wait_for_selector("#results .recommendation-card", timeout=10000)
        time.sleep(0.5)  # allow layout to settle

        # Check breakdown table wrapper exists
        breakdown_wrapper = page.query_selector(".breakdown-section")
        check("Breakdown section present at mobile", breakdown_wrapper is not None)

        # Check row labels exist
        row_labels = page.query_selector_all(".row-label")
        check(
            "Row labels present for sticky columns",
            len(row_labels) > 0,
            f"Found {len(row_labels)} row labels",
        )

        shot_path = str(_SCREENSHOT_DIR / "mobile.png")
        page.screenshot(path=shot_path)
        print(f"  Screenshot: {shot_path}")

        # Restore viewport
        page.set_viewport_size({"width": 1280, "height": 720})

        # Close the default context before dark/light mode checks
        context.close()

        # === CHECK 8: Dark mode verification ===
        verify_dark_mode(browser)

        # === CHECK 9: Light mode verification ===
        verify_light_mode(browser)

        # === CHECK 10-16: Comma formatting verification ===
        verify_comma_formatting(browser)

        # === CHECK 17-22: Export/Import verification ===
        verify_export_import(browser)

        # === CHECK 23-29: Detailed period breakdown verification ===
        verify_detailed_breakdown(browser)

        browser.close()

    # Summary
    print(f"\n=== RESULTS: {len(PASSED)} passed, {len(FAILED)} failed ===")
    if FAILED:
        print("FAILURES:")
        for f in FAILED:
            print(f"  - {f}")
        sys.exit(1)
    else:
        print("All Playwright browser checks passed.")
        sys.exit(0)


if __name__ == "__main__":
    main()
