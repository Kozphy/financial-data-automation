"""Deterministic row and amount reconciliation for a single pipeline run.

Amounts are converted from available values using Decimal(str(value)).
This verifies conservation *after ingestion*, not source-byte monetary precision:
upstream pandas floating-point parsing can already have lost precision.
"""
from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any
import pandas as pd


def _amounts(frame: pd.DataFrame) -> tuple[Decimal, int]:
    if "amount" not in frame.columns:
        raise ValueError("Reconciliation requires an amount column")
    total = Decimal("0")
    unknown = 0
    for value in frame["amount"]:
        if pd.isna(value) or (isinstance(value, str) and not value.strip()):
            unknown += 1
            continue
        try:
            amount = Decimal(str(value))
        except (InvalidOperation, ValueError, TypeError):
            unknown += 1
            continue
        if not amount.is_finite():
            unknown += 1
            continue
        total += amount
    return total, unknown


def reconcile_amounts(
    source: pd.DataFrame,
    cleaned: pd.DataFrame,
    rejected: pd.DataFrame,
) -> dict[str, Any]:
    """Fail closed on missing rows or numeric variance; disclose unparseable values."""
    input_total, input_unknown = _amounts(source)
    clean_total, clean_unknown = _amounts(cleaned)
    reject_total, reject_unknown = _amounts(rejected)
    row_variance = len(source) - len(cleaned) - len(rejected)
    variance = input_total - clean_total - reject_total
    if row_variance != 0:
        raise ValueError(f"Row reconciliation failed: variance={row_variance}")
    if variance != 0:
        raise ValueError(f"Amount reconciliation failed: variance={variance}")
    if clean_unknown != 0:
        raise ValueError("Clean output contains unparseable amounts")
    # Unknown source amounts remain quarantined, not silently assigned zero.
    if input_unknown != reject_unknown:
        raise ValueError("Unparseable source amounts were not fully quarantined")
    return {
        "input_amount_total": str(input_total),
        "clean_amount_total": str(clean_total),
        "rejected_amount_total": str(reject_total),
        "amount_variance": str(variance),
        "row_variance": int(row_variance),
        "unparseable_source_amounts": int(input_unknown),
        "completeness": "partial" if input_unknown else "complete",
        "basis": "post_ingestion_decimal_from_available_values",
    }
