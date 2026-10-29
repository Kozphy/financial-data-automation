"""End-to-end coverage for Traditional Chinese exports and zh-TW reports."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from financial_data_automation.pipeline import run_pipeline

ROOT = Path(__file__).resolve().parents[1]
ZH_SAMPLE = ROOT / "data" / "sample" / "sample_transactions_zh_tw.csv"
BANK_SAMPLE = ROOT / "data" / "sample" / "sample_bank_statement_zh_tw.csv"
EN_SAMPLE = ROOT / "data" / "sample" / "sample_transactions.csv"


def test_english_sample_counts_stay_the_same(tmp_path: Path) -> None:
    result = run_pipeline(
        EN_SAMPLE,
        output_dir=tmp_path / "out",
        evidence_path=tmp_path / "audit.jsonl",
    )
    assert result["input_rows"] == 9
    assert result["clean_rows"] == 4
    assert result["rejected_rows"] == 5
    assert result["quality_score"] == round(4 / 9, 6)
    cleaned = pd.read_excel(tmp_path / "out" / "cleaned_data.xlsx")
    assert "transaction_id" in cleaned.columns
    assert "交易編號" not in cleaned.columns
    record = json.loads((tmp_path / "audit.jsonl").read_text(encoding="utf-8").splitlines()[0])
    assert record["language"] == "en"
    assert record["status"] == "success"


def test_chinese_sample_with_roc_dates(tmp_path: Path) -> None:
    result = run_pipeline(
        ZH_SAMPLE,
        output_dir=tmp_path / "out",
        evidence_path=tmp_path / "audit.jsonl",
        language="zh-TW",
    )
    assert result["input_rows"] == 8
    assert result["clean_rows"] == 4
    assert result["rejected_rows"] == 4
    cleaned = pd.read_excel(tmp_path / "out" / "cleaned_data.xlsx")
    assert "交易編號" in cleaned.columns
    assert "金額" in cleaned.columns
    amounts = set(cleaned["金額"].tolist())
    assert 1200.50 in amounts
    assert -300 in amounts or -300.0 in amounts
    assert 1500 in amounts
    dates = set(pd.to_datetime(cleaned["日期"]).dt.strftime("%Y-%m-%d"))
    assert "2024-05-01" in dates
    assert "2024-05-08" in dates
    assert "2024-08-01" in dates

    rejected = pd.read_excel(tmp_path / "out" / "rejected_rows.xlsx")
    assert "剔除原因" in rejected.columns
    assert "剔除說明" in rejected.columns
    assert set(rejected["剔除原因"]) == {
        "exact_duplicate_row",
        "missing_description",
        "invalid_date",
        "invalid_amount",
    }
    assert "完全重複列" in set(rejected["剔除說明"])

    summary = pd.read_excel(tmp_path / "out" / "financial_summary.xlsx", sheet_name="摘要")
    assert "合計金額" in summary.columns
    assert "毛利" in summary.columns
    quality = pd.read_csv(tmp_path / "out" / "quality_report.csv")
    assert "檢查項目" in quality.columns
    assert "說明" in quality.columns
    assert "無效日期" in set(quality["說明"])


def test_bank_statement_debit_credit(tmp_path: Path) -> None:
    result = run_pipeline(
        BANK_SAMPLE,
        output_dir=tmp_path / "out",
        evidence_path=tmp_path / "audit.jsonl",
    )
    assert result["clean_rows"] == 2
    assert result["rejected_rows"] == 0
    assert result["column_mapping"]["debit_credit_combined"] is True
    cleaned = pd.read_excel(tmp_path / "out" / "cleaned_data.xlsx")
    assert set(cleaned["amount"].tolist()) == {50000, -1250}
    assert "餘額" in cleaned.columns
    assert "debit" in cleaned.columns
    assert "credit" in cleaned.columns


def test_big5_csv_round_trip(tmp_path: Path) -> None:
    frame = pd.DataFrame(
        {
            "交易編號": ["A1"],
            "交易日期": ["113/05/01"],
            "摘要": ["測試"],
            "金額": ["NT$10"],
        }
    )
    path = tmp_path / "big5.csv"
    path.write_bytes(frame.to_csv(index=False).encode("cp950"))
    result = run_pipeline(
        path,
        output_dir=tmp_path / "out",
        evidence_path=tmp_path / "audit.jsonl",
    )
    assert result["clean_rows"] == 1
    cleaned = pd.read_excel(tmp_path / "out" / "cleaned_data.xlsx")
    assert cleaned.loc[0, "description"] == "測試"
    assert cleaned.loc[0, "amount"] == 10
    assert pd.Timestamp(cleaned.loc[0, "date"]) == pd.Timestamp("2024-05-01")


def test_language_switch_does_not_change_clean_count(tmp_path: Path) -> None:
    english = run_pipeline(
        ZH_SAMPLE,
        output_dir=tmp_path / "en",
        evidence_path=tmp_path / "en.jsonl",
        language="en",
    )
    chinese = run_pipeline(
        ZH_SAMPLE,
        output_dir=tmp_path / "zh",
        evidence_path=tmp_path / "zh.jsonl",
        language="zh_TW",
    )
    assert english["clean_rows"] == chinese["clean_rows"]
    assert english["quality_score"] == chinese["quality_score"]


def test_missing_file_samples_exist() -> None:
    assert ZH_SAMPLE.exists()
    assert BANK_SAMPLE.exists()
