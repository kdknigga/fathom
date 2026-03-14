"""
Tests verifying Pydantic BaseModel structure and mutability constraints.

Covers REFACTOR-01 (all 7 domain models are Pydantic BaseModel subclasses)
and REFACTOR-05 (output models are frozen, input models remain mutable).
"""

from decimal import Decimal

from pydantic import BaseModel

from fathom.models import (
    Caveat,
    ComparisonResult,
    FinancingOption,
    GlobalSettings,
    MonthlyDataPoint,
    OptionResult,
    OptionType,
    PromoResult,
)

# ---------------------------------------------------------------------------
# REFACTOR-01: All 7 domain models are Pydantic BaseModel subclasses
# ---------------------------------------------------------------------------


def test_all_domain_models_are_pydantic_basemodel_subclasses() -> None:
    """All 7 domain models inherit from pydantic BaseModel (REFACTOR-01)."""
    models = [
        FinancingOption,
        GlobalSettings,
        MonthlyDataPoint,
        OptionResult,
        PromoResult,
        Caveat,
        ComparisonResult,
    ]
    for model in models:
        assert issubclass(model, BaseModel), (
            f"{model.__name__} is not a Pydantic BaseModel subclass"
        )


# ---------------------------------------------------------------------------
# REFACTOR-05: Output models are frozen; input models remain mutable
# ---------------------------------------------------------------------------


def test_output_models_have_frozen_config() -> None:
    """All 5 output models declare frozen=True in model_config (REFACTOR-05)."""
    output_models = [
        MonthlyDataPoint,
        OptionResult,
        PromoResult,
        Caveat,
        ComparisonResult,
    ]
    for model in output_models:
        frozen = model.model_config.get("frozen")
        assert frozen is True, (
            f"{model.__name__} model_config does not have frozen=True"
        )


def test_input_models_are_not_frozen() -> None:
    """Both input models do not have frozen=True in model_config (REFACTOR-05)."""
    input_models = [FinancingOption, GlobalSettings]
    for model in input_models:
        frozen = model.model_config.get("frozen")
        assert frozen is not True, (
            f"{model.__name__} should not be frozen but has frozen={frozen}"
        )


def test_financing_option_allows_mutation() -> None:
    """FinancingOption instance allows attribute reassignment at runtime (REFACTOR-05)."""
    option = FinancingOption(
        option_type=OptionType.CASH,
        label="Original Label",
        purchase_price=Decimal(10000),
    )
    option.label = "Updated Label"
    assert option.label == "Updated Label"


def test_global_settings_allows_mutation() -> None:
    """GlobalSettings instance allows attribute reassignment at runtime (REFACTOR-05)."""
    settings = GlobalSettings(return_rate=Decimal("0.07"))
    settings.inflation_enabled = True
    assert settings.inflation_enabled


# ---------------------------------------------------------------------------
# DETAIL-01: MonthlyDataPoint per-period cost factor fields
# ---------------------------------------------------------------------------


def test_monthly_data_point_accepts_new_cost_factor_fields() -> None:
    """MonthlyDataPoint accepts opportunity_cost, inflation_adjustment, tax_savings."""
    dp = MonthlyDataPoint(
        month=1,
        payment=Decimal("500.00"),
        interest_portion=Decimal("50.00"),
        principal_portion=Decimal("450.00"),
        remaining_balance=Decimal("9550.00"),
        investment_balance=Decimal(0),
        cumulative_cost=Decimal("500.00"),
        opportunity_cost=Decimal("12.50"),
        inflation_adjustment=Decimal("1.25"),
        tax_savings=Decimal("11.00"),
    )
    assert dp.opportunity_cost == Decimal("12.50")
    assert dp.inflation_adjustment == Decimal("1.25")
    assert dp.tax_savings == Decimal("11.00")


def test_monthly_data_point_defaults_new_fields_to_zero() -> None:
    """MonthlyDataPoint defaults new fields to Decimal(0) for backward compat."""
    dp = MonthlyDataPoint(
        month=1,
        payment=Decimal("500.00"),
        interest_portion=Decimal("50.00"),
        principal_portion=Decimal("450.00"),
        remaining_balance=Decimal("9550.00"),
        investment_balance=Decimal(0),
        cumulative_cost=Decimal("500.00"),
    )
    assert dp.opportunity_cost == Decimal(0)
    assert dp.inflation_adjustment == Decimal(0)
    assert dp.tax_savings == Decimal(0)
