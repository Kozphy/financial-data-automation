#!/usr/bin/env python3
"""Render docs/before-after.png from a real pipeline run on the synthetic sample.

Dev-only helper (requires matplotlib, which is NOT a runtime dependency):

    python -m pip install matplotlib
    python scripts/generate_sample_data.py
    python scripts/make_readme_image.py

The pipeline is executed into a temporary directory so the repository's
data/processed/ outputs and evidence/audit.jsonl are not touched.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from financial_data_automation.ingestion import load_data  # noqa: E402
from financial_data_automation.pipeline import run_pipeline  # noqa: E402

SAMPLE = ROOT / "data" / "sample" / "sample_transactions.xlsx"
OUT = ROOT / "docs" / "before-after.png"

REASON_LABELS = {
    "exact_duplicate_row": "Duplicate row",
    "duplicate_transaction_id": "Duplicate transaction ID",
    "invalid_date": "Invalid date",
    "invalid_amount": "Invalid amount",
    "missing_description": "Missing description",
    "missing_transaction_id": "Missing transaction ID",
}
# Which displayed column holds the problem for each reason (None = whole row).
REASON_COLUMN = {
    "exact_duplicate_row": None,
    "duplicate_transaction_id": 0,
    "missing_transaction_id": 0,
    "invalid_date": 1,
    "missing_description": 2,
    "invalid_amount": 3,
}

RED_ROW = "#fde2e2"
RED_CELL = "#f4a3a3"
GREEN_HDR = "#2e7d32"
GREY_HDR = "#455a64"
RED_HDR = "#b23b3b"


def _fmt_amount(v) -> str:
    try:
        return f"{float(v):,.2f}"
    except (TypeError, ValueError):
        return "" if pd.isna(v) else str(v)


def _fmt_text(v) -> str:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return "(blank)"
    if isinstance(v, pd.Timestamp):
        return v.strftime("%Y-%m-%d")
    return str(v)


def _draw_table(ax, rows, col_labels, col_widths, header_color, cell_colors=None,
                font_size=10.5, row_height=None):
    table = ax.table(
        cellText=rows,
        colLabels=col_labels,
        colWidths=col_widths,
        cellLoc="left",
        loc="upper center",
        cellColours=cell_colors,
    )
    table.auto_set_font_size(False)
    table.set_fontsize(font_size)
    for (r, _c), cell in table.get_celld().items():
        cell.set_edgecolor("#cfd8dc")
        if row_height:
            cell.set_height(row_height)
        if r == 0:
            cell.set_facecolor(header_color)
            cell.set_text_props(color="white", weight="bold")
    return table


def _assign_raw_rows(raw: pd.DataFrame, cleaned: pd.DataFrame, rejected: pd.DataFrame) -> dict[int, str]:
    """Map raw row index -> reject_reason using the pipeline's own outputs."""
    ids = raw["transaction_id"].astype(str).str.strip()
    unassigned = list(raw.index)
    # Cleaned rows keep the first occurrence of each transaction_id.
    for tid in cleaned["transaction_id"].astype(str).str.strip():
        match = next(i for i in unassigned if ids[i] == tid)
        unassigned.remove(match)
    reasons: dict[int, str] = {}
    for tid, reason in zip(rejected["transaction_id"].astype(str).str.strip(), rejected["reject_reason"]):
        match = next(i for i in unassigned if ids[i] == tid)
        unassigned.remove(match)
        reasons[match] = reason
    return reasons


def main() -> int:
    if not SAMPLE.exists():
        print("Sample data missing; run scripts/generate_sample_data.py first.", file=sys.stderr)
        return 1

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        result = run_pipeline(SAMPLE, output_dir=tmp_path / "processed",
                              evidence_path=tmp_path / "audit.jsonl")
        processed = tmp_path / "processed"
        cleaned = pd.read_excel(processed / "cleaned_data.xlsx")
        rejected = pd.read_excel(processed / "rejected_rows.xlsx")
        monthly = pd.read_excel(processed / "financial_summary.xlsx", sheet_name="monthly")
        summary = pd.read_excel(processed / "financial_summary.xlsx", sheet_name="summary").iloc[0]

    # Raw values exactly as they appear in the input file (no type coercion).
    raw_original = pd.read_excel(SAMPLE, dtype=str)
    raw = load_data(SAMPLE)
    reasons = _assign_raw_rows(raw, cleaned, rejected)

    fig = plt.figure(figsize=(17, 9), dpi=150)
    fig.patch.set_facecolor("white")
    fig.suptitle("Same file, one command:  python run_pipeline.py sample_transactions.xlsx",
                 fontsize=13, color="#37474f", y=0.975)

    # ---------------- BEFORE ----------------
    ax_b = fig.add_axes([0.02, 0.08, 0.45, 0.80])
    ax_b.axis("off")
    ax_b.set_title("Before", fontsize=24, weight="bold", color=RED_HDR, loc="left")
    ax_b.text(0.0, 0.985, "Raw export as received (synthetic sample, 9 rows)",
              transform=ax_b.transAxes, fontsize=11.5, color="#455a64", va="bottom")
    cols = ["Transaction ID", "Date", "Description", "Amount"]
    rows, colors = [], []
    for i in raw_original.index:
        # Show the values exactly as stored in the file (unformatted).
        vals = [_fmt_text(raw_original.at[i, c]) for c in cols]
        rows.append(vals)
        if i in reasons:
            bad_col = REASON_COLUMN.get(reasons[i])
            colors.append([RED_CELL if bad_col in (None, j) else RED_ROW for j in range(4)])
        else:
            colors.append(["white"] * 4)
    _draw_table(ax_b, rows, cols, [0.2, 0.18, 0.42, 0.16], GREY_HDR, colors,
                font_size=11, row_height=0.072)
    ax_b.text(0.0, 0.25,
              "Red rows = problems hidden in the spreadsheet:\n"
              "duplicate rows, a reused transaction ID, a blank description,\n"
              "\"not-a-date\" in the Date column, and \"abc\" in the Amount column.",
              transform=ax_b.transAxes, fontsize=11, color=RED_HDR, va="top")

    # ---------------- AFTER ----------------
    ax_a = fig.add_axes([0.52, 0.08, 0.46, 0.80])
    ax_a.axis("off")
    ax_a.set_title("After", fontsize=24, weight="bold", color=GREEN_HDR, loc="left")

    score = result["quality_score"] * 100
    ax_a.text(0.0, 0.985,
              f"{result['clean_rows']} clean rows  |  {result['rejected_rows']} quarantined with a reason  |  "
              f"quality score {score:.1f}%",
              transform=ax_a.transAxes, fontsize=11.5, color="#455a64", va="bottom")

    # Cleaned data
    ax_c = fig.add_axes([0.52, 0.565, 0.46, 0.25])
    ax_c.axis("off")
    ax_c.text(0.0, 1.0, "cleaned_data.xlsx", transform=ax_c.transAxes, fontsize=11,
              weight="bold", color=GREEN_HDR, va="bottom")
    c_rows = [[r.transaction_id, _fmt_text(pd.Timestamp(r.date)), r.description, _fmt_amount(r.amount)]
              for r in cleaned.itertuples()]
    _draw_table(ax_c, c_rows, cols, [0.2, 0.18, 0.42, 0.16], GREEN_HDR, font_size=10.5, row_height=0.17)

    # Rejected rows
    ax_r = fig.add_axes([0.52, 0.29, 0.46, 0.25])
    ax_r.axis("off")
    ax_r.text(0.0, 1.0, "rejected_rows.xlsx  (nothing deleted: every bad row kept with its reason)",
              transform=ax_r.transAxes, fontsize=11, weight="bold", color=RED_HDR, va="bottom")
    r_rows = [[r.transaction_id, _fmt_text(r.description), REASON_LABELS.get(r.reject_reason, r.reject_reason)]
              for r in rejected.itertuples()]
    _draw_table(ax_r, r_rows, ["Transaction ID", "Description", "Reject reason"],
                [0.2, 0.42, 0.34], RED_HDR, font_size=10.5, row_height=0.145)

    # Monthly totals + summary
    ax_m = fig.add_axes([0.52, 0.04, 0.22, 0.20])
    ax_m.axis("off")
    ax_m.text(0.0, 1.0, "financial_summary.xlsx: monthly", transform=ax_m.transAxes, fontsize=11,
              weight="bold", color=GREY_HDR, va="bottom")
    m_rows = [[m.month, _fmt_amount(m.total_amount), str(int(m.record_count))] for m in monthly.itertuples()]
    _draw_table(ax_m, m_rows, ["Month", "Total", "Rows"], [0.36, 0.38, 0.22], GREY_HDR,
                font_size=10.5, row_height=0.2)

    ax_s = fig.add_axes([0.76, 0.04, 0.22, 0.20])
    ax_s.axis("off")
    ax_s.text(0.0, 1.0, "financial_summary.xlsx: summary", transform=ax_s.transAxes, fontsize=11,
              weight="bold", color=GREY_HDR, va="bottom")
    margin = summary.get("gross_margin")
    s_rows = [
        ["Total amount", _fmt_amount(summary["total_amount"])],
        ["Gross profit", _fmt_amount(summary.get("gross_profit"))],
        ["Gross margin", "" if pd.isna(margin) else f"{margin * 100:.1f}%"],
        ["Quality score", f"{score:.1f}%"],
    ]
    _draw_table(ax_s, s_rows, ["Metric", "Value"], [0.55, 0.4], GREY_HDR, font_size=10.5, row_height=0.16)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, dpi=110, facecolor="white")
    print(f"Wrote {OUT.relative_to(ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
