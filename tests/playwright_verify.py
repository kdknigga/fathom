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

        # === CHECK 5: Responsive layout at 375px ===
        print("\n--- Check 5: Responsive layout (375px) ---")
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
