"""Tests for schema validation."""

from __future__ import annotations

import pandas as pd

from financial_data_automation.validation import validate_schema


def test_missing_required_columns() -> None:
    df = pd.DataFrame({"transaction_id": ["1"], "amount": [1]})
    report = validate_schema(df)
    assert "date" in report["missing_columns"]
    assert "description" in report["missing_columns"]
    assert report["ok"] is False


def test_invalid_dates() -> None:
    df = pd.DataFrame(
        {
            "transaction_id": ["1", "2"],
            "date": ["2026-01-01", "not-a-date"],
            "description": ["a", "b"],
            "amount": [1, 2],
        }
    )
    report = validate_schema(df)
    assert report["invalid_dates"] == 1


def test_invalid_amounts() -> None:
    df = pd.DataFrame(
        {
            "transaction_id": ["1", "2"],
            "date": ["2026-01-01", "2026-01-02"],
            "description": ["a", "b"],
            "amount": [10, "abc"],
        }
    )
    report = validate_schema(df)
    assert report["invalid_amounts"] == 1


def test_duplicate_detection() -> None:
    df = pd.DataFrame(
        {
            "transaction_id": ["1", "1", "2"],
            "date": ["2026-01-01", "2026-01-02", "2026-01-03"],
            "description": ["a", "b", "c"],
            "amount": [1, 2, 3],
        }
    )
    report = validate_schema(df)
    assert report["duplicate_transaction_ids"] == 2
