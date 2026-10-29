"""ROC dates and TWD amount parsing."""

from __future__ import annotations

import math

import pandas as pd

from financial_data_automation.formats import parse_amount_value, parse_date_value
from financial_data_automation.validation import validate_schema


def test_roc_and_gregorian_dates() -> None:
    assert parse_date_value("113/05/01") == pd.Timestamp("2024-05-01")
    assert parse_date_value("113年5月1日") == pd.Timestamp("2024-05-01")
    assert parse_date_value("民國113年5月1日") == pd.Timestamp("2024-05-01")
    assert parse_date_value("１１３／０８／０１") == pd.Timestamp("2024-08-01")
    assert parse_date_value("2024年5月1日") == pd.Timestamp("2024-05-01")
    assert parse_date_value("2026-01-01") == pd.Timestamp("2026-01-01")
    assert parse_date_value("113/13/01") is pd.NaT or pd.isna(parse_date_value("113/13/01"))
    assert pd.isna(parse_date_value("not-a-date"))


def test_twd_amounts() -> None:
    assert parse_amount_value("NT$1,234.50") == 1234.50
    assert parse_amount_value("NT$ (1,234.50)") == -1234.50
    assert parse_amount_value("(1,234.50)") == -1234.50
    assert parse_amount_value("（１，２３４．５０）") == -1234.50
    assert parse_amount_value("１，５００") == 1500
    assert parse_amount_value(120.5) == 120.5
    assert parse_amount_value("120.5") == 120.5
    assert parse_amount_value("-500") == -500
    assert math.isnan(parse_amount_value("abc"))
    assert math.isnan(parse_amount_value(""))
    assert math.isnan(parse_amount_value("  "))


def test_validation_accepts_roc_date_and_twd_amount() -> None:
    report = validate_schema(
        pd.DataFrame(
            {
                "transaction_id": ["1", "2"],
                "date": ["113/05/01", "not-a-date"],
                "description": ["辦公用品", "交通費"],
                "amount": ["NT$1,200.50", "abc"],
            }
        )
    )
    assert report["invalid_dates"] == 1
    assert report["invalid_amounts"] == 1
    parsed = report["coerced_frame"]
    assert parsed.loc[0, "date"] == pd.Timestamp("2024-05-01")
    assert parsed.loc[0, "amount"] == 1200.50
