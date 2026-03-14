"""
Tests for tooltip ? button presence and keyboard-accessibility markup (TIPS-01, 02, 03).

Uses Flask test client DOM assertions to verify the HTML structure that enables
tooltip behavior: .tip buttons with popovertarget, matching popover divs, and
keyboard-accessible bracket rows.

TIPS-01: ? buttons on form field labels open popovers
TIPS-02: ? buttons on result breakdown rows open popovers
TIPS-03: Keyboard accessibility -- .tip buttons focusable, bracket rows keyboard-navigable
"""

from pathlib import Path

from flask.testing import FlaskClient

# Minimal valid form data shared across result-page tests
_VALID_FORM = {
    "purchase_price": "10000",
    "options[0][type]": "cash",
    "options[0][label]": "Cash",
    "options[1][type]": "traditional_loan",
    "options[1][label]": "Loan",
    "options[1][apr]": "5.99",
    "options[1][term_months]": "24",
    "options[1][down_payment]": "0",
    "return_preset": "0.07",
    "return_rate_custom": "",
    "inflation_rate": "3",
    "tax_rate": "22",
}

_STATIC_DIR = Path(__file__).parent.parent / "src" / "fathom" / "static"


class TestFormFieldTooltipButtons:
    """
    Verify tooltip ? buttons render on form field labels (TIPS-01).

    Each .tip button must have a popovertarget attribute pointing to a
    matching popover div so the browser Popover API can open it on click.
    """

    def test_global_settings_tax_rate_has_tip_button(self, client: FlaskClient):
        """GET / includes a .tip button for the Marginal Tax Rate field."""
        response = client.get("/")
        html = response.data.decode()
        assert 'popovertarget="tip-tax-rate"' in html

    def test_global_settings_tax_rate_popover_div_exists(self, client: FlaskClient):
        """GET / includes the matching popover div for the tax rate tooltip."""
        response = client.get("/")
        html = response.data.decode()
        assert 'id="tip-tax-rate"' in html
        assert "popover" in html

    def test_global_settings_inflation_rate_has_tip_button(self, client: FlaskClient):
        """GET / includes a .tip button for the Inflation Rate field."""
        response = client.get("/")
        html = response.data.decode()
        assert 'popovertarget="tip-inflation-rate"' in html

    def test_global_settings_return_rate_has_tip_button(self, client: FlaskClient):
        """GET / includes a .tip button for the Investment Return Rate field."""
        response = client.get("/")
        html = response.data.decode()
        assert 'popovertarget="tip-return-rate"' in html

    def test_option_apr_field_has_tip_button(self, client: FlaskClient):
        """GET / includes a .tip button for the APR field on option cards."""
        response = client.get("/")
        html = response.data.decode()
        # APR tooltip IDs are scoped per option index: tip-apr-0, tip-apr-1, etc.
        assert 'popovertarget="tip-apr-' in html

    def test_option_term_field_has_tip_button(self, client: FlaskClient):
        """GET / includes a .tip button for the Loan Term field on option cards."""
        response = client.get("/")
        html = response.data.decode()
        assert 'popovertarget="tip-term-' in html

    def test_tip_buttons_have_class_tip(self, client: FlaskClient):
        """GET / .tip buttons carry the correct CSS class for styling."""
        response = client.get("/")
        html = response.data.decode()
        assert 'class="tip"' in html

    def test_tip_buttons_have_aria_label(self, client: FlaskClient):
        """GET / .tip buttons carry aria-label for screen reader accessibility."""
        response = client.get("/")
        html = response.data.decode()
        assert 'aria-label="What is' in html

    def test_tip_buttons_are_type_button(self, client: FlaskClient):
        """GET / .tip buttons have type='button' to prevent form submission."""
        response = client.get("/")
        html = response.data.decode()
        # All tip buttons should be type="button", not type="submit"
        assert 'type="button" class="tip"' in html

    def test_label_with_tip_wrapper_present(self, client: FlaskClient):
        """GET / label-with-tip divs wrap labels and tip buttons together."""
        response = client.get("/")
        html = response.data.decode()
        assert 'class="label-with-tip"' in html

    def test_popover_content_divs_have_tooltip_content_class(self, client: FlaskClient):
        """GET / popover divs carry class='tooltip-content' for CSS targeting."""
        response = client.get("/")
        html = response.data.decode()
        assert 'class="tooltip-content"' in html


class TestResultBreakdownTooltipButtons:
    """
    Verify tooltip ? buttons render on breakdown table metric rows (TIPS-02).

    Each row with tooltip text must have a .tip button with popovertarget
    and a matching popover div with the explanation.
    """

    def test_breakdown_rows_have_tip_metric_buttons(self, client: FlaskClient):
        """POST /compare breakdown table rows include .tip buttons with metric IDs."""
        response = client.post("/compare", data=_VALID_FORM)
        assert response.status_code == 200
        html = response.data.decode()
        assert 'popovertarget="tip-metric-' in html

    def test_breakdown_rows_have_popover_divs(self, client: FlaskClient):
        """POST /compare breakdown table rows include popover divs with metric IDs."""
        response = client.post("/compare", data=_VALID_FORM)
        html = response.data.decode()
        assert 'id="tip-metric-' in html

    def test_breakdown_table_has_label_with_tip_wrappers(self, client: FlaskClient):
        """POST /compare breakdown rows wrap labels in label-with-tip containers."""
        response = client.post("/compare", data=_VALID_FORM)
        html = response.data.decode()
        assert 'class="label-with-tip"' in html

    def test_recommendation_card_has_true_total_cost_tooltip(self, client: FlaskClient):
        """POST /compare recommendation card includes True Total Cost tooltip button."""
        response = client.post("/compare", data=_VALID_FORM)
        html = response.data.decode()
        assert "tip-rec-true-total-cost" in html

    def test_recommendation_tooltip_has_popover_div(self, client: FlaskClient):
        """POST /compare recommendation tooltip has matching popover div."""
        response = client.post("/compare", data=_VALID_FORM)
        html = response.data.decode()
        assert 'id="tip-rec-true-total-cost"' in html


class TestTooltipKeyboardAccessibility:
    """
    Verify keyboard-accessibility markup for tooltips and bracket rows (TIPS-03).

    TIPS-03 requires: Tab to .tip button, Enter to open, Escape to close.
    The HTML Popover API handles Enter/Escape natively for <button popovertarget>.
    Bracket rows must be keyboard-navigable via tabindex and role="button".
    """

    def test_tip_buttons_are_natively_keyboard_focusable(self, client: FlaskClient):
        """GET / .tip buttons are <button> elements which are focusable by default."""
        response = client.get("/")
        html = response.data.decode()
        # Native <button> elements are in the tab order without explicit tabindex
        assert '<button type="button" class="tip"' in html

    def test_tip_buttons_have_focus_visible_rule_in_css(self):
        """style.css includes :focus-visible rule for .tip buttons (keyboard UX)."""
        css = (_STATIC_DIR / "style.css").read_text()
        assert ".tip:focus-visible" in css

    def test_bracket_rows_have_tabindex_for_keyboard_focus(self, client: FlaskClient):
        """GET / bracket rows have tabindex='0' to allow keyboard navigation."""
        response = client.get("/")
        html = response.data.decode()
        assert 'tabindex="0"' in html

    def test_bracket_rows_have_role_button_for_keyboard_activation(
        self, client: FlaskClient
    ):
        """GET / bracket rows have role='button' for screen reader and keyboard UX."""
        response = client.get("/")
        html = response.data.decode()
        assert 'role="button"' in html

    def test_bracket_rows_have_aria_label(self, client: FlaskClient):
        """GET / bracket rows have aria-label describing the action."""
        response = client.get("/")
        html = response.data.decode()
        assert 'aria-label="Select' in html
        assert "% tax rate" in html

    def test_tooltips_js_loaded_in_page(self, client: FlaskClient):
        """GET / page includes tooltips.js which handles keyboard Enter/Space on bracket rows."""
        response = client.get("/")
        html = response.data.decode()
        assert "tooltips.js" in html

    def test_tooltips_js_handles_keyboard_enter_on_bracket_rows(self):
        """tooltips.js keydown handler responds to Enter key on .bracket-row elements."""
        js = (_STATIC_DIR / "tooltips.js").read_text()
        assert "Enter" in js
        assert "bracket-row" in js

    def test_popover_api_enables_escape_dismiss(self, client: FlaskClient):
        """GET / popover elements use the HTML Popover API (Escape dismiss is native)."""
        response = client.get("/")
        html = response.data.decode()
        # Native popover attribute enables Escape key dismissal automatically
        assert "popover" in html
        assert "tooltip-content" in html
