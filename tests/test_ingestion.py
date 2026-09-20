"""Tests for ingestion helpers."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from financial_data_automation.ingestion import load_data, normalize_column_names


def test_normalize_column_names() -> None:
    df = pd.DataFrame({"Transaction ID": [1], " Unit Price ": [2]})
    out = normalize_column_names(df)
    assert list(out.columns) == ["transaction_id", "unit_price"]


def test_load_csv(tmp_path: Path) -> None:
    path = tmp_path / "tx.csv"
    pd.DataFrame(
        {
            "Transaction ID": ["A1"],
            "Date": ["2026-01-01"],
            "Description": ["x"],
            "Amount": [10],
        }
    ).to_csv(path, index=False)
    df = load_data(path)
    assert "transaction_id" in df.columns
    assert len(df) == 1


def test_load_excel(tmp_path: Path) -> None:
    path = tmp_path / "tx.xlsx"
    pd.DataFrame(
        {
            "Transaction ID": ["A1"],
            "Date": ["2026-01-01"],
            "Description": ["x"],
            "Amount": [10],
        }
    ).to_excel(path, index=False)
    df = load_data(path)
    assert list(df.columns) == [
        "transaction_id",
        "date",
        "description",
        "amount",
    ]


def test_missing_file(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_data(tmp_path / "missing.csv")


def test_unsupported_format(tmp_path: Path) -> None:
    path = tmp_path / "tx.json"
    path.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="Unsupported"):
        load_data(path)
