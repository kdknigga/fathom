"""
Tax bracket reference data for the tax guidance widget.

Source: IRS Revenue Procedure 2024-40 (for tax year 2025).
Provides the seven federal income tax brackets with income ranges
for Single and Married Filing Jointly filing statuses.
"""

from __future__ import annotations

#: 2025 federal income tax brackets from IRS Rev. Proc. 2024-40.
#: Each entry has a marginal rate and income range boundaries for
#: Single and Married Filing Jointly (MFJ) filing statuses.
#: A ``None`` max indicates no upper limit (top bracket).
TAX_BRACKETS_2025: list[dict[str, int | None]] = [
    {
        "rate": 10,
        "single_min": 0,
        "single_max": 11_925,
        "mfj_min": 0,
        "mfj_max": 23_850,
    },
    {
        "rate": 12,
        "single_min": 11_926,
        "single_max": 48_475,
        "mfj_min": 23_851,
        "mfj_max": 96_950,
    },
    {
        "rate": 22,
        "single_min": 48_476,
        "single_max": 103_350,
        "mfj_min": 96_951,
        "mfj_max": 206_700,
    },
    {
        "rate": 24,
        "single_min": 103_351,
        "single_max": 197_300,
        "mfj_min": 206_701,
        "mfj_max": 394_600,
    },
    {
        "rate": 32,
        "single_min": 197_301,
        "single_max": 250_525,
        "mfj_min": 394_601,
        "mfj_max": 501_050,
    },
    {
        "rate": 35,
        "single_min": 250_526,
        "single_max": 626_350,
        "mfj_min": 501_051,
        "mfj_max": 751_600,
    },
    {
        "rate": 37,
        "single_min": 626_351,
        "single_max": None,
        "mfj_min": 751_601,
        "mfj_max": None,
    },
]
