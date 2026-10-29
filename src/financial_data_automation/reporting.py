"""Write cleaned data, rejects, and financial reports to disk."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from financial_data_automation.i18n import (
    Language,
    check_label,
    localize_frame,
    normalize_language,
    reject_label,
    sheet_names,
)


def write_reports(
    cleaned_df: pd.DataFrame,
    rejected_df: pd.DataFrame,
    summary: dict[str, Any],
    monthly_df: pd.DataFrame,
    quality_rows: list[dict[str, Any]],
    output_dir: str | Path,
    *,
    language: str = "en",
) -> list[str]:
    """
    Persist pipeline outputs under ``output_dir``.

    Returns relative-style output filenames (as Path names under output_dir).
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    lang = normalize_language(language)

    cleaned_path = out / "cleaned_data.xlsx"
    rejected_path = out / "rejected_rows.xlsx"
    summary_path = out / "financial_summary.xlsx"
    quality_path = out / "quality_report.csv"

    cleaned_out = localize_frame(cleaned_df, lang)
    rejected_out = _localize_rejected(rejected_df, lang)
    summary_out = localize_frame(pd.DataFrame([summary]), lang)
    monthly_out = localize_frame(monthly_df, lang)
    quality_out = _localize_quality(quality_rows, lang)
    summary_sheet, monthly_sheet, quality_sheet = sheet_names(lang)

    cleaned_out.to_excel(cleaned_path, index=False)
    rejected_out.to_excel(rejected_path, index=False)

    with pd.ExcelWriter(summary_path, engine="openpyxl") as writer:
        summary_out.to_excel(writer, sheet_name=summary_sheet, index=False)
        monthly_out.to_excel(writer, sheet_name=monthly_sheet, index=False)
        quality_out.to_excel(writer, sheet_name=quality_sheet, index=False)

    quality_out.to_csv(quality_path, index=False)

    return [
        cleaned_path.name,
        rejected_path.name,
        summary_path.name,
        quality_path.name,
    ]


def _localize_rejected(rejected_df: pd.DataFrame, language: Language) -> pd.DataFrame:
    out = rejected_df.copy()
    if language == "zh-TW" and "reject_reason" in out.columns:
        out["reject_reason_label"] = [
            reject_label(value, language) for value in out["reject_reason"].tolist()
        ]
    return localize_frame(out, language)


def _localize_quality(quality_rows: list[dict[str, Any]], language: Language) -> pd.DataFrame:
    quality_df = pd.DataFrame(quality_rows)
    if language == "zh-TW" and "check" in quality_df.columns:
        quality_df.insert(
            1,
            "label",
            [check_label(str(value), language) for value in quality_df["check"].tolist()],
        )
    return localize_frame(quality_df, language)


def verify_outputs(output_dir: str | Path, expected_names: list[str]) -> list[str]:
    """Return list of missing expected output file names."""
    out = Path(output_dir)
    missing = [name for name in expected_names if not (out / name).exists()]
    return missing
