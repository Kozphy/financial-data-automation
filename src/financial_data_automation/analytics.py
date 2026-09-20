"""Deterministic financial metrics for cleaned transaction data."""

from __future__ import annotations

from typing import Any

import pandas as pd


def compute_financial_summary(df: pd.DataFrame) -> dict[str, Any]:
    """
    Compute core financial metrics from cleaned rows.

    Gross profit/margin use only rows with both amount and cost present.
    Missing cost is not treated as zero. Margin denominator is that subset's
    total amount; returns None when the denominator is zero.
    """
    if df.empty:
        summary: dict[str, Any] = {
            "record_count": 0,
            "total_amount": 0.0,
            "average_amount": None,
            "minimum_amount": None,
            "maximum_amount": None,
        }
    else:
        amounts = pd.to_numeric(df["amount"], errors="coerce")
        summary = {
            "record_count": int(len(df)),
            "total_amount": float(amounts.sum()),
            "average_amount": float(amounts.mean()),
            "minimum_amount": float(amounts.min()),
            "maximum_amount": float(amounts.max()),
        }

    if "cost" in df.columns and not df.empty:
        cost = pd.to_numeric(df["cost"], errors="coerce")
        amount = pd.to_numeric(df["amount"], errors="coerce")
        # Do not invent cost=0 for missing values; only rows with both sides contribute.
        usable = amount.notna() & cost.notna()
        if usable.any():
            gross_profit = float((amount[usable] - cost[usable]).sum())
            summary["gross_profit"] = gross_profit
            total_amount = float(amount[usable].sum())
            if total_amount == 0:
                summary["gross_margin"] = None
            else:
                summary["gross_margin"] = float(gross_profit / total_amount)
        else:
            summary["gross_profit"] = None
            summary["gross_margin"] = None

    return summary


def compute_monthly_totals(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate total amount by calendar month."""
    if df.empty or "date" not in df.columns:
        return pd.DataFrame(columns=["month", "total_amount", "record_count"])

    working = df.copy()
    working["month"] = pd.to_datetime(working["date"]).dt.to_period("M").astype(str)
    grouped = (
        working.groupby("month", as_index=False)
        .agg(total_amount=("amount", "sum"), record_count=("amount", "size"))
        .sort_values("month")
        .reset_index(drop=True)
    )
    return grouped


def compute_quality_score(input_rows: int, clean_rows: int) -> float:
    """
    Quality score = valid (cleaned) records / total input records.

    Returns 0.0 when there are no input rows.
    """
    if input_rows <= 0:
        return 0.0
    return round(clean_rows / input_rows, 6)
