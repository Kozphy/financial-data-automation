"""Write cleaned data, rejects, and financial reports to disk."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

DISCLAIMER = (
    "Calculated from the supplied file. "
    "This is not an audit opinion, a forecast, or a guarantee of financial results."
)
_AMOUNT_FORMAT = "#,##0.00"
_RATIO_FORMAT = "0.00%"
_HEADER_FILL = PatternFill("solid", fgColor="D9E2F3")
_AMOUNT_HEADERS = {
    "total_amount",
    "average_amount",
    "minimum_amount",
    "maximum_amount",
    "gross_profit",
    "amount",
}
_RATIO_HEADERS = {"gross_margin"}


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

    _format_summary_workbook(summary_path)
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


def _format_summary_workbook(path: Path) -> None:
    from openpyxl import load_workbook

    workbook = load_workbook(path)
    notice = workbook.create_sheet("notice", 0)
    notice["A1"] = DISCLAIMER
    notice["A1"].alignment = Alignment(wrap_text=True)
    notice.column_dimensions["A"].width = 88
    for name in ("summary", "monthly", "quality"):
        _format_sheet(workbook[name])
    workbook.save(path)


def _format_sheet(sheet) -> None:
    sheet.freeze_panes = "A2"
    sheet.auto_filter.ref = sheet.dimensions
    for cell in sheet[1]:
        cell.font = Font(bold=True)
        cell.fill = _HEADER_FILL
        if isinstance(cell.value, str):
            letter = get_column_letter(cell.column)
            sheet.column_dimensions[letter].width = max(len(cell.value) + 2, 14)
    headers = [cell.value for cell in sheet[1]]
    for index, header in enumerate(headers, start=1):
        number_format = None
        if header in _AMOUNT_HEADERS:
            number_format = _AMOUNT_FORMAT
        elif header in _RATIO_HEADERS:
            number_format = _RATIO_FORMAT
        if number_format is None:
            continue
        for row in range(2, sheet.max_row + 1):
            sheet.cell(row, index).number_format = number_format

