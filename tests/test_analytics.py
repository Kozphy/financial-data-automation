"""Tests for analytics helpers."""

from __future__ import annotations

import pandas as pd
import pytest

from financial_data_automation.analytics import (
    compute_financial_summary,
    compute_quality_score,
)


def test_financial_summary() -> None:
    df = pd.DataFrame(
        {
            "transaction_id": ["1", "2"],
            "date": pd.to_datetime(["2026-01-01", "2026-01-02"]),
            "description": ["a", "b"],
            "amount": [100.0, 50.0],
            "cost": [40.0, 10.0],
        }
    )
    summary = compute_financial_summary(df)
    assert summary["record_count"] == 2
    assert summary["total_amount"] == 150.0
    assert summary["average_amount"] == 75.0
    assert summary["minimum_amount"] == 50.0
    assert summary["maximum_amount"] == 100.0
    assert summary["gross_profit"] == 100.0
    assert summary["gross_margin"] == pytest.approx(100.0 / 150.0)


def test_quality_score() -> None:
    assert compute_quality_score(100, 95) == 0.95
    assert compute_quality_score(0, 0) == 0.0
