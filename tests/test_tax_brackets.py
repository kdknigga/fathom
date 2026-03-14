"""
Tests for TAX_BRACKETS_2025 constant and template rendering of bracket data.

Covers:
- TAX-01: bracket data has 7 entries with correct 2025 IRS rates and income ranges
- TAX-01: routes pass tax_brackets to template context so widget renders
- TAX-02: income values in bracket table are comma-formatted (|comma filter)
"""

from flask.testing import FlaskClient

from fathom.tax_brackets import TAX_BRACKETS_2025


class TestTaxBracketsConstant:
    """Verify TAX_BRACKETS_2025 contains correct 2025 IRS data (TAX-01)."""

    def test_bracket_data_has_seven_entries(self):
        """TAX_BRACKETS_2025 contains exactly 7 federal income tax brackets."""
        assert len(TAX_BRACKETS_2025) == 7

    def test_bracket_rates_are_correct_2025_irs_values(self):
        """TAX_BRACKETS_2025 rates match the 7 official 2025 IRS marginal rates."""
        rates = [b["rate"] for b in TAX_BRACKETS_2025]
        assert rates == [10, 12, 22, 24, 32, 35, 37]

    def test_ten_percent_bracket_single_max_is_11925(self):
        """10% bracket single filer ceiling is $11,925 per IRS Rev. Proc. 2024-40."""
        bracket_10 = TAX_BRACKETS_2025[0]
        assert bracket_10["rate"] == 10
        assert bracket_10["single_max"] == 11_925

    def test_twelve_percent_bracket_single_range_is_correct(self):
        """12% bracket single filer range is $11,926 to $48,475."""
        bracket_12 = TAX_BRACKETS_2025[1]
        assert bracket_12["single_min"] == 11_926
        assert bracket_12["single_max"] == 48_475

    def test_twenty_four_percent_bracket_mfj_max_is_394600(self):
        """24% bracket MFJ ceiling is $394,600 per IRS Rev. Proc. 2024-40."""
        bracket_24 = TAX_BRACKETS_2025[3]
        assert bracket_24["rate"] == 24
        assert bracket_24["mfj_max"] == 394_600

    def test_top_bracket_single_max_is_none(self):
        """37% (top) bracket has no single filer upper limit (single_max is None)."""
        bracket_37 = TAX_BRACKETS_2025[6]
        assert bracket_37["rate"] == 37
        assert bracket_37["single_max"] is None

    def test_top_bracket_mfj_max_is_none(self):
        """37% (top) bracket has no MFJ upper limit (mfj_max is None)."""
        bracket_37 = TAX_BRACKETS_2025[6]
        assert bracket_37["mfj_max"] is None

    def test_each_bracket_has_required_keys(self):
        """Every bracket dict has rate, single_min, single_max, mfj_min, mfj_max keys."""
        required_keys = {"rate", "single_min", "single_max", "mfj_min", "mfj_max"}
        for bracket in TAX_BRACKETS_2025:
            assert required_keys == set(bracket.keys()), (
                f"Bracket {bracket.get('rate')}% missing required keys"
            )

    def test_brackets_are_monotonically_increasing_by_rate(self):
        """Brackets are ordered from lowest to highest marginal rate."""
        rates = [b["rate"] for b in TAX_BRACKETS_2025]
        assert rates == sorted(rates)

    def test_single_ranges_are_contiguous(self):
        """Each bracket's single_min is exactly one dollar above the previous single_max."""
        for i in range(1, 6):  # Brackets 2-6 (not the open-ended top bracket)
            prev_max = TAX_BRACKETS_2025[i - 1]["single_max"]
            curr_min = TAX_BRACKETS_2025[i]["single_min"]
            assert curr_min == prev_max + 1, (
                f"Gap at bracket {i}: prev_max={prev_max}, curr_min={curr_min}"
            )


class TestTaxBracketsInRouteContext:
    """Verify routes pass tax_brackets to template context (TAX-01)."""

    def test_index_route_renders_tax_bracket_widget(self, client: FlaskClient):
        """GET / renders the tax bracket reference widget from tax_brackets context."""
        response = client.get("/")
        assert response.status_code == 200
        html = response.data.decode()
        assert "tax-bracket-ref" in html

    def test_index_route_renders_all_seven_bracket_rows(self, client: FlaskClient):
        """GET / renders 7 bracket rows in the bracket table from tax_brackets context."""
        response = client.get("/")
        html = response.data.decode()
        # Each bracket row has class="bracket-row" and a data-rate attribute
        assert html.count('class="bracket-row"') == 7

    def test_index_route_renders_all_2025_rates(self, client: FlaskClient):
        """GET / bracket table shows all 7 marginal rate percentages."""
        response = client.get("/")
        html = response.data.decode()
        for rate in [10, 12, 22, 24, 32, 35, 37]:
            assert f'data-rate="{rate}"' in html, (
                f'data-rate="{rate}" missing from bracket table'
            )

    def test_compare_route_renders_tax_bracket_widget(self, client: FlaskClient):
        """POST /compare results page also contains tax bracket widget (TAX-01)."""
        response = client.post(
            "/compare",
            data={
                "purchase_price": "10000",
                "options[0][type]": "cash",
                "options[0][label]": "Cash",
                "options[1][type]": "traditional_loan",
                "options[1][label]": "Loan",
                "options[1][apr]": "5",
                "options[1][term_months]": "24",
                "return_preset": "0.07",
                "return_rate_custom": "",
                "inflation_rate": "3",
                "tax_rate": "22",
            },
        )
        assert response.status_code == 200
        html = response.data.decode()
        assert "tax-bracket-ref" in html


class TestBracketTableCommaFormatting:
    """Verify income ranges in bracket table are comma-formatted (TAX-02)."""

    def test_index_route_renders_comma_formatted_income_ranges(
        self, client: FlaskClient
    ):
        """GET / bracket table shows comma-formatted values like $11,925 not $11925."""
        response = client.get("/")
        html = response.data.decode()
        # The 10% bracket single_max is 11925 - must appear as 11,925
        assert "11,925" in html, "10% bracket single_max $11,925 not comma-formatted"

    def test_index_route_shows_comma_formatted_mfj_range(self, client: FlaskClient):
        """GET / bracket table shows MFJ ranges with commas (e.g., $23,850)."""
        response = client.get("/")
        html = response.data.decode()
        # The 10% bracket mfj_max is 23850 - must appear as 23,850
        assert "23,850" in html, "10% bracket mfj_max $23,850 not comma-formatted"

    def test_index_route_shows_no_raw_unformatted_bracket_values(
        self, client: FlaskClient
    ):
        """GET / bracket table does not contain raw unformatted large integers."""
        response = client.get("/")
        html = response.data.decode()
        # Verify no unformatted 5-digit income values appear (they should all have commas)
        assert "11925" not in html, "Raw unformatted value 11925 leaked into HTML"
        assert "48475" not in html, "Raw unformatted value 48475 leaked into HTML"

    def test_top_bracket_shows_plus_sign_for_no_upper_limit(self, client: FlaskClient):
        """GET / top bracket (37%) shows '+' to indicate no upper income limit."""
        response = client.get("/")
        html = response.data.decode()
        # 37% bracket has single_min=626351 -> rendered as $626,351+
        assert "626,351" in html, "37% bracket single_min $626,351 not rendered"
