"""
Formatting utilities for Fathom template rendering.

Provides Jinja filter functions for formatting monetary values
with comma-separated thousands.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation


def _comma_format_str(value: str) -> str:
    """
    Format a numeric string with comma-separated thousands.

    Strips dollar signs, commas, and spaces, then re-formats. Preserves
    trailing zeros in decimal places and passes through non-numeric
    values unchanged.

    Args:
        value: A numeric string (e.g., "25000", "25000.50", "25,000").

    Returns:
        Comma-formatted string, or original value if non-numeric.

    """
    if not value or not value.strip():
        return value

    cleaned = value.strip().replace("$", "").replace(",", "").replace(" ", "")
    if not cleaned:
        return value

    try:
        dec = Decimal(cleaned)
    except InvalidOperation:
        return value

    # Pure integer with no decimal point in input
    if dec == int(dec) and "." not in cleaned:
        return f"{int(dec):,}"

    # Preserve exact decimal representation (including trailing zeros)
    if "." in cleaned:
        int_part, dec_part = cleaned.split(".", 1)
        formatted_int = f"{int(int_part):,}"
        return f"{formatted_int}.{dec_part}" if dec_part else formatted_int

    return f"{int(cleaned):,}"


def comma_format(value: str | int | float) -> str:
    """
    Format a numeric value with comma-separated thousands.

    Handles already-formatted input (idempotent), preserves trailing
    zeros in decimal places, and passes through non-numeric values
    unchanged.  Accepts int/float in addition to strings.

    Args:
        value: A numeric string (e.g., "25000", "25000.50", "25,000"),
            an int, or a float.

    Returns:
        Comma-formatted string, or original value if non-numeric.

    """
    if isinstance(value, int):
        return f"{value:,}"
    if isinstance(value, float):
        return f"{value:,.2f}"
    return _comma_format_str(value)
