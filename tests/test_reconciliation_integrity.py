"""Regression controls for row/amount conservation and artifact hashing."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from financial_data_automation.integrity import hash_outputs, sha256_file, verify_hashes
from financial_data_automation.pipeline import run_pipeline
from financial_data_automation.reconciliation import reconcile_amounts


def test_decimal_reconciliation_exact_tenths() -> None:
    source = pd.DataFrame({"amount": ["0.1", "0.2", "0.3"]})
    cleaned = source.iloc[:2].copy()
    rejected = source.iloc[2:].copy()
    result = reconcile_amounts(source, cleaned, rejected)
    assert result["input_amount_total"] == "0.6"
    assert result["amount_variance"] == "0.0"
    assert result["completeness"] == "complete"


def test_reconciliation_detects_omitted_row() -> None:
    frame = pd.DataFrame({"amount": [10, 20]})
    with pytest.raises(ValueError, match="Row reconciliation"):
        reconcile_amounts(frame, frame.iloc[:1], frame.iloc[:0])


def test_reconciliation_discloses_unparseable_amount() -> None:
    source = pd.DataFrame({"amount": ["10", "invalid"]})
    result = reconcile_amounts(source, source.iloc[:1], source.iloc[1:])
    assert result["unparseable_source_amounts"] == 1
    assert result["completeness"] == "partial"


def test_reconciliation_detects_amount_mutation() -> None:
    source = pd.DataFrame({"amount": ["10"]})
    changed = pd.DataFrame({"amount": ["11"]})
    with pytest.raises(ValueError, match="Amount reconciliation"):
        reconcile_amounts(source, changed, source.iloc[:0])


def test_hashes_detect_modification(tmp_path: Path) -> None:
    path = tmp_path / "report.csv"
    path.write_text("a,b\n1,2\n", encoding="utf-8")
    first = sha256_file(path)
    hashes = hash_outputs(tmp_path, ["report.csv"])
    assert verify_hashes(tmp_path, hashes) == []
    path.write_text("a,b\n1,3\n", encoding="utf-8")
    assert sha256_file(path) != first
    assert verify_hashes(tmp_path, hashes) == ["report.csv"]


def test_pipeline_emits_reconciliation_and_sha256(tmp_path: Path) -> None:
    source = tmp_path / "transactions.csv"
    pd.DataFrame({
        "transaction_id": ["A", "B"],
        "date": ["2026-01-01", "not-a-date"],
        "description": ["valid", "reject"],
        "amount": [100, 50],
    }).to_csv(source, index=False)
    out = tmp_path / "processed"
    log = tmp_path / "audit.jsonl"
    result = run_pipeline(source, output_dir=out, evidence_path=log)
    record = json.loads(log.read_text(encoding="utf-8").splitlines()[0])
    assert record["reconciliation"]["input_amount_total"] == "150"
    assert record["reconciliation"]["clean_amount_total"] == "100"
    assert record["reconciliation"]["rejected_amount_total"] == "50"
    assert record["reconciliation"]["amount_variance"] == "0"
    assert record["input_sha256"] == sha256_file(source)
    assert record["output_sha256"]
    assert verify_hashes(out, record["output_sha256"]) == []
    assert result["reconciliation"] == record["reconciliation"]
