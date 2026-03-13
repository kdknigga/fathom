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
            ".visually-hidden table:has(caption:text('True Total Cost'))"
        )
        check("Bar chart data table found", bar_table is not None)
        if bar_table:
            # Verify parent div has visually-hidden class
            bar_parent = bar_table.evaluate(
                "el => el.parentElement.classList.contains('visually-hidden')"
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
            ".visually-hidden table:has(caption:text('Cumulative'))"
        )
        check("Line chart data table found", line_table is not None)
        if line_table:
            # Verify parent div has visually-hidden class
            line_parent = line_table.evaluate(
                "el => el.parentElement.classList.contains('visually-hidden')"
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
