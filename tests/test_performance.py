"""Performance tests ensuring response times stay within acceptable bounds."""

import time

from fathom.app import create_app


class TestComparePerformance:
    """Verify POST /compare responds within 300ms (PERF-01 requirement)."""

    def _make_compare_request(self, client):
        """Submit a valid comparison form and return (response, elapsed_seconds)."""
        form_data = {
            "purchase_price": "10000",
            "options[0][type]": "cash",
            "options[0][label]": "Pay in Full",
            "options[1][type]": "traditional_loan",
            "options[1][label]": "Standard Loan",
            "options[1][apr]": "5.99",
            "options[1][term_months]": "36",
            "options[1][down_payment]": "1000",
            "return_preset": "0.07",
            "return_rate_custom": "",
            "inflation_enabled": "",
            "inflation_rate": "3",
            "tax_enabled": "",
            "tax_rate": "22",
        }
        start = time.perf_counter()
        response = client.post("/compare", data=form_data)
        elapsed = time.perf_counter() - start
        return response, elapsed

    def test_compare_returns_200(self):
        """POST /compare with valid data returns 200."""
        app = create_app()
        app.config["TESTING"] = True
        with app.test_client() as client:
            response, _ = self._make_compare_request(client)
            assert response.status_code == 200

    def test_compare_under_300ms_average(self):
        """Average response time over 5 requests is under 300ms."""
        app = create_app()
        app.config["TESTING"] = True
        with app.test_client() as client:
            # Warm up
            self._make_compare_request(client)

            times = []
            for _ in range(5):
                _, elapsed = self._make_compare_request(client)
                times.append(elapsed)

            avg = sum(times) / len(times)
            assert avg < 0.3, f"Average response time {avg:.3f}s exceeds 300ms limit"
