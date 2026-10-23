"""CLI output directory is honored."""

from pathlib import Path

import pandas as pd

from financial_data_automation.cli import main


def test_cli_writes_the_formatted_summary_to_the_requested_directory(tmp_path: Path) -> None:
    source = tmp_path / "input.xlsx"
    output = tmp_path / "reports"
    pd.DataFrame(
        {
            "Transaction ID": ["T1"],
            "Date": ["2026-01-01"],
            "Description": ["alpha"],
            "Amount": [10.0],
        }
    ).to_excel(source, index=False)

    code = main([str(source), "--output", str(output), "--evidence", str(tmp_path / "audit.jsonl")])
    assert code == 0
    assert (output / "financial_summary.xlsx").is_file()
    assert (output / "quality_report.csv").is_file()
