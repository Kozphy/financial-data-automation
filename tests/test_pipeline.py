"""End-to-end pipeline tests."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from financial_data_automation.pipeline import run_pipeline


def _write_valid_workbook(path: Path) -> None:
    pd.DataFrame(
        {
            "Transaction ID": ["T1", "T2"],
            "Date": ["2026-01-01", "2026-01-02"],
            "Description": ["alpha", "beta"],
            "Amount": [10.0, 20.0],
            "Cost": [1.0, 2.0],
        }
    ).to_excel(path, index=False)


def test_pipeline_success(tmp_path: Path) -> None:
    input_path = tmp_path / "ok.xlsx"
    output_dir = tmp_path / "processed"
    evidence = tmp_path / "audit.jsonl"
    _write_valid_workbook(input_path)

    result = run_pipeline(
        input_path,
        output_dir=output_dir,
        evidence_path=evidence,
    )
    assert result["status"] == "success"
    assert result["input_rows"] == 2
    assert result["clean_rows"] == 2
    assert result["rejected_rows"] == 0
    assert result["quality_score"] == 1.0
    for name in result["output_names"]:
        assert (output_dir / name).exists()
    lines = evidence.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["status"] == "success"
    assert record["input_file"] == "ok.xlsx"
    assert "Users" not in json.dumps(record)


def test_pipeline_duplicates_removed_counts_both_kinds(tmp_path: Path) -> None:
    input_path = tmp_path / "dups.xlsx"
    output_dir = tmp_path / "processed"
    evidence = tmp_path / "audit.jsonl"
    pd.DataFrame(
        {
            "Transaction ID": ["T1", "T1", "T2", "T2"],
            "Date": ["2026-01-01", "2026-01-01", "2026-01-02", "2026-01-03"],
            "Description": ["same", "same", "alpha", "beta"],
            "Amount": [10.0, 10.0, 20.0, 30.0],
        }
    ).to_excel(input_path, index=False)

    result = run_pipeline(
        input_path,
        output_dir=output_dir,
        evidence_path=evidence,
    )
    record = json.loads(evidence.read_text(encoding="utf-8").strip().splitlines()[0])
    # One exact duplicate of T1, plus the later T2 duplicate-id row.
    assert result["clean_rows"] == 2
    assert result["rejected_rows"] == 2
    assert record["duplicates_removed"] == 2


def test_pipeline_failure_writes_evidence(tmp_path: Path) -> None:
    input_path = tmp_path / "bad.xlsx"
    output_dir = tmp_path / "processed"
    evidence = tmp_path / "audit.jsonl"
    pd.DataFrame({"foo": [1]}).to_excel(input_path, index=False)

    with pytest.raises(ValueError, match="Missing required columns"):
        run_pipeline(
            input_path,
            output_dir=output_dir,
            evidence_path=evidence,
        )

    lines = evidence.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["status"] == "failed"
    assert record["error_type"] == "ValueError"
    assert record["input_file"] == "bad.xlsx"
