"""
Shared test fixtures for the fathom test suite.

Provides reusable financing options, global settings, and helper
objects used across all test modules.
"""

from decimal import Decimal

import pytest
from flask import Flask
from flask.testing import FlaskClient

from fathom.app import create_app
from fathom.models import FinancingOption, GlobalSettings, OptionType


@pytest.fixture
def app() -> Flask:
    """Create a Flask application configured for testing."""
    test_app = create_app()
    test_app.config["TESTING"] = True
    return test_app


@pytest.fixture
def client(app: Flask) -> FlaskClient:
    """Create a Flask test client for making requests."""
    return app.test_client()


@pytest.fixture
def standard_loan() -> FinancingOption:
    """Create a standard $10,000 traditional loan at 6% APR for 36 months."""
    return FinancingOption(
        option_type=OptionType.TRADITIONAL_LOAN,
        label="Standard Loan",
        purchase_price=Decimal(10000),
        apr=Decimal("0.06"),
        term_months=36,
    )


@pytest.fixture
def cash_option() -> FinancingOption:
    """Create a $10,000 cash purchase option."""
    return FinancingOption(
        option_type=OptionType.CASH,
        label="Pay in Full",
        purchase_price=Decimal(10000),
    )


@pytest.fixture
def promo_zero_percent() -> FinancingOption:
    """
    Create a $10,000 zero-percent promo with deferred interest.

    12-month term, 24.99% post-promo APR, deferred interest enabled.
    """
    return FinancingOption(
        option_type=OptionType.PROMO_ZERO_PERCENT,
        label="0% Promo",
        purchase_price=Decimal(10000),
        term_months=12,
        post_promo_apr=Decimal("0.2499"),
        deferred_interest=True,
    )


@pytest.fixture
def default_settings() -> GlobalSettings:
    """Create default settings with 7% return, no inflation, no tax."""
    return GlobalSettings(
        return_rate=Decimal("0.07"),
    )


@pytest.fixture
def settings_with_inflation() -> GlobalSettings:
    """Create settings with 7% return and 3% inflation enabled."""
    return GlobalSettings(
        return_rate=Decimal("0.07"),
        inflation_enabled=True,
        inflation_rate=Decimal("0.03"),
    )


@pytest.fixture
def settings_with_tax() -> GlobalSettings:
    """Create settings with 7% return and 22% tax enabled."""
    return GlobalSettings(
        return_rate=Decimal("0.07"),
        tax_enabled=True,
        tax_rate=Decimal("0.22"),
    )
