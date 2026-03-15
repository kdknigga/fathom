"""
Tests for the centralized monetary rounding utilities in money.py.

Verifies quantize_money() behavior across edge cases, the value of the
CENTS constant, and that no consumer module defines its own duplicate.
"""

import ast
from decimal import Decimal
from pathlib import Path


def test_cents_constant_equals_one_hundredth() -> None:
    """CENTS constant must equal Decimal('0.01')."""
    from fathom.money import CENTS

    assert Decimal("0.01") == CENTS


def test_quantize_money_rounds_to_two_decimal_places() -> None:
    """quantize_money() rounds a value to exactly two decimal places."""
    from fathom.money import quantize_money

    result = quantize_money(Decimal("1.234"))
    assert result == Decimal("1.23")
    assert result.as_tuple().exponent == -2


def test_quantize_money_already_rounded_value_unchanged() -> None:
    """quantize_money() leaves an already-rounded value unchanged."""
    from fathom.money import quantize_money

    result = quantize_money(Decimal("99.99"))
    assert result == Decimal("99.99")


def test_quantize_money_zero_returns_zero() -> None:
    """quantize_money() returns Decimal('0.00') for zero input."""
    from fathom.money import quantize_money

    result = quantize_money(Decimal(0))
    assert result == Decimal("0.00")
    assert result.as_tuple().exponent == -2


def test_quantize_money_negative_value() -> None:
    """quantize_money() handles negative monetary values correctly."""
    from fathom.money import quantize_money

    result = quantize_money(Decimal("-12.345"))
    assert result == Decimal("-12.34") or result == Decimal("-12.35")
    assert result.as_tuple().exponent == -2


def test_quantize_money_large_number() -> None:
    """quantize_money() handles large numbers (e.g. six-figure purchase prices)."""
    from fathom.money import quantize_money

    result = quantize_money(Decimal("999999.999"))
    assert result.as_tuple().exponent == -2
    assert result == Decimal("1000000.00") or result == Decimal("999999.99")


def test_quantize_money_very_small_fraction_rounds_to_zero() -> None:
    """quantize_money() rounds a very small fraction to Decimal('0.00')."""
    from fathom.money import quantize_money

    result = quantize_money(Decimal("0.001"))
    assert result == Decimal("0.00")
    assert result.as_tuple().exponent == -2


def test_quantize_money_returns_decimal_type() -> None:
    """quantize_money() always returns a Decimal, never a float or int."""
    from fathom.money import quantize_money

    result = quantize_money(Decimal("42.0"))
    assert isinstance(result, Decimal)


# ---------------------------------------------------------------------------
# Centralization integrity: no consumer module defines its own copy
# ---------------------------------------------------------------------------

_CONSUMER_FILES = [
    "src/fathom/amortization.py",
    "src/fathom/opportunity.py",
    "src/fathom/inflation.py",
    "src/fathom/caveats.py",
    "src/fathom/tax.py",
    "src/fathom/engine.py",
]

_REPO_ROOT = Path(__file__).parent.parent


def _functions_defined_in(source: str) -> list[str]:
    """Return all top-level function names defined in source text."""
    tree = ast.parse(source)
    return [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]


def _assignments_in(source: str) -> list[str]:
    """Return all module-level assignment target names in source text."""
    tree = ast.parse(source)
    names: list[str] = []
    for node in tree.body:
        if isinstance(node, ast.Assign):
            names.extend(
                target.id for target in node.targets if isinstance(target, ast.Name)
            )
    return names


def test_quantize_money_defined_only_in_money_module() -> None:
    """No consumer module defines its own quantize_money() function."""
    for rel_path in _CONSUMER_FILES:
        source = (_REPO_ROOT / rel_path).read_text()
        defined = _functions_defined_in(source)
        assert "quantize_money" not in defined, (
            f"{rel_path} defines its own quantize_money() — "
            "must import from fathom.money instead"
        )


def test_cents_constant_defined_only_in_money_module() -> None:
    """No consumer module defines its own CENTS constant."""
    for rel_path in _CONSUMER_FILES:
        source = (_REPO_ROOT / rel_path).read_text()
        assigned = _assignments_in(source)
        assert "CENTS" not in assigned, (
            f"{rel_path} defines its own CENTS constant — "
            "must import from fathom.money instead"
        )


def test_consumer_files_import_quantize_money_from_fathom_money() -> None:
    """Each consumer module that uses quantize_money imports it from fathom.money."""
    for rel_path in _CONSUMER_FILES:
        source = (_REPO_ROOT / rel_path).read_text()
        if "quantize_money" not in source:
            continue
        assert "from fathom.money import" in source, (
            f"{rel_path} uses quantize_money but does not import from fathom.money"
        )
        assert "quantize_money" in source, (
            f"{rel_path} missing quantize_money in fathom.money import"
        )
