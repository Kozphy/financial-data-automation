"""Write cleaned data, rejects, and financial reports to disk."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd


def write_reports(
    cleaned_df: pd.DataFrame,
    rejected_df: pd.DataFrame,
    summary: dict[str, Any],
    monthly_df: pd.DataFrame,
    quality_rows: list[dict[str, Any]],
    output_dir: str | Path,
) -> list[str]:
    """
    Persist pipeline outputs under ``output_dir``.

    Returns relative-style output filenames (as Path names under output_dir).
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    cleaned_path = out / "cleaned_data.xlsx"
    rejected_path = out / "rejected_rows.xlsx"
    summary_path = out / "financial_summary.xlsx"
    quality_path = out / "quality_report.csv"

    cleaned_df.to_excel(cleaned_path, index=False)
    rejected_df.to_excel(rejected_path, index=False)

    summary_df = pd.DataFrame([summary])
    quality_df = pd.DataFrame(quality_rows)
    with pd.ExcelWriter(summary_path, engine="openpyxl") as writer:
        summary_df.to_excel(writer, sheet_name="summary", index=False)
        monthly_df.to_excel(writer, sheet_name="monthly", index=False)
        quality_df.to_excel(writer, sheet_name="quality", index=False)

    quality_df.to_csv(quality_path, index=False)

    return [
        cleaned_path.name,
        rejected_path.name,
        summary_path.name,
        quality_path.name,
    ]


def verify_outputs(output_dir: str | Path, expected_names: list[str]) -> list[str]:
    """Return list of missing expected output file names."""
    out = Path(output_dir)
    missing = [name for name in expected_names if not (out / name).exists()]
    return missing
