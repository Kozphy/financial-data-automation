"""Tests for cleaning quarantine behavior."""

from __future__ import annotations

import pandas as pd

from financial_data_automation.cleaning import clean_data
from financial_data_automation.validation import validate_schema


def test_cleaning_returns_rejected_rows() -> None:
    df = pd.DataFrame(
        {
            "transaction_id": ["1", "1", "2", "3"],
            "date": ["2026-01-01", "2026-01-01", "bad-date", "2026-01-03"],
            "description": ["ok", "ok", "travel", ""],
            "amount": [10, 10, 20, "xyz"],
        }
    )
    report = validate_schema(df)
    cleaned, rejected = clean_data(report["coerced_frame"])
    assert "reject_reason" in rejected.columns
    # Cleaning must partition rows: nothing silently dropped.
    assert len(cleaned) + len(rejected) == len(df)
    assert len(cleaned) == 1
    assert len(rejected) == 3
    assert set(rejected["reject_reason"]) == {
        "exact_duplicate_row",
        "invalid_date",
        "invalid_amount",
    }
