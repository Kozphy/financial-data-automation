"""Schema and data-quality validation for financial transactions."""

from __future__ import annotations

from typing import Any

import pandas as pd

REQUIRED_COLUMNS = ("transaction_id", "date", "description", "amount")
NON_NEGATIVE_OPTIONAL = ("quantity", "unit_price", "cost")


def _blank_string_mask(series: pd.Series) -> pd.Series:
    """True for non-null values that are empty/whitespace-only strings."""
    return series.map(lambda v: isinstance(v, str) and v.strip() == "")


def _missing_required_mask(series: pd.Series) -> pd.Series:
    """Completeness mask: nulls and blank/whitespace-only strings."""
    return series.isna() | _blank_string_mask(series)


def validate_schema(df: pd.DataFrame) -> dict[str, Any]:
    """
    Validate required columns and coerce date/amount where possible.

    Returns a structured report. Does not mutate the caller's DataFrame
    beyond returning a working copy with attempted coercions.
    """
    working = df.copy()
    missing_columns = [c for c in REQUIRED_COLUMNS if c not in working.columns]

    report: dict[str, Any] = {
        "missing_columns": missing_columns,
        "invalid_dates": 0,
        "invalid_amounts": 0,
        "duplicate_transaction_ids": 0,
        "null_required_fields": {},
        "negative_optional_fields": {},
        "inconsistent_quantity_price": 0,
        "coerced_frame": working,
        "ok": len(missing_columns) == 0,
    }

    if missing_columns:
        return report

    # Completeness is measured on the pre-coercion values so it is not
    # inflated by validity failures that become NaT/NaN after parsing.
    report["null_required_fields"] = {
        col: int(_missing_required_mask(working[col]).sum())
        for col in REQUIRED_COLUMNS
    }

    parsed_dates = pd.to_datetime(working["date"], errors="coerce")
    originally_present = working["date"].notna() & ~_blank_string_mask(working["date"])
    failed_parse = originally_present & parsed_dates.isna()
    report["invalid_dates"] = int(failed_parse.sum())
    working["date"] = parsed_dates

    parsed_amounts = pd.to_numeric(working["amount"], errors="coerce")
    present_non_empty = working["amount"].notna() & ~_blank_string_mask(working["amount"])
    failed_amt = present_non_empty & parsed_amounts.isna()
    report["invalid_amounts"] = int(failed_amt.sum())
    working["amount"] = parsed_amounts

    if working["transaction_id"].notna().any():
        dup_mask = working["transaction_id"].duplicated(keep=False) & working[
            "transaction_id"
        ].notna()
        # Count of rows whose transaction_id value is not unique (includes first occurrence).
        report["duplicate_transaction_ids"] = int(dup_mask.sum())

    negatives: dict[str, int] = {}
    for col in NON_NEGATIVE_OPTIONAL:
        if col in working.columns:
            numeric = pd.to_numeric(working[col], errors="coerce")
            working[col] = numeric
            negatives[col] = int((numeric.notna() & (numeric < 0)).sum())
    report["negative_optional_fields"] = negatives

    if "quantity" in working.columns and "unit_price" in working.columns:
        expected = working["quantity"] * working["unit_price"]
        # Compare to amount when both quantity and unit_price are present
        comparable = (
            working["quantity"].notna()
            & working["unit_price"].notna()
            & working["amount"].notna()
        )
        if comparable.any():
            mismatch = comparable & (
                (expected - working["amount"]).abs() > 1e-6
            )
            report["inconsistent_quantity_price"] = int(mismatch.sum())

    report["coerced_frame"] = working
    report["ok"] = True
    return report
