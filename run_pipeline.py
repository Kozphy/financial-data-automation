#!/usr/bin/env python3
"""CLI entry point for the financial data automation pipeline."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Allow `python run_pipeline.py ...` after `pip install -r requirements.txt`
# without requiring an editable package install.
_SRC = Path(__file__).resolve().parent / "src"
if _SRC.is_dir() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from financial_data_automation.i18n import CLI_STRINGS_ZH, normalize_language
from financial_data_automation.pipeline import run_pipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="run_pipeline.py",
        description=(
            "Clean a financial CSV or Excel export into audit-ready reports. "
            "Headers from bank statements, QuickBooks, and shops such as Shopee "
            "are mapped onto transaction_id, date, description, and amount."
        ),
    )
    parser.add_argument("input", help="Input .csv or .xlsx file")
    parser.add_argument(
        "--mapping",
        "-m",
        metavar="FILE",
        help="Optional .csv, .json, or .xlsx column mapping (columns: source, target)",
    )
    parser.add_argument(
        "--language",
        "-l",
        default="en",
        help="Report language: en (default) or zh-TW",
    )
    parser.add_argument(
        "--output-dir",
        "-o",
        metavar="DIR",
        help="Output directory (default: data/processed)",
    )
    parser.add_argument(
        "--evidence",
        "-e",
        metavar="FILE",
        help="Append-only audit JSONL path (default: evidence/audit.jsonl)",
    )
    return parser


def _print_english(result: dict[str, object]) -> None:
    score_pct = float(result["quality_score"]) * 100
    print("Pipeline completed successfully.")
    print()
    print(f"Input rows:      {result['input_rows']}")
    print(f"Clean rows:       {result['clean_rows']}")
    print(f"Rejected rows:     {result['rejected_rows']}")
    print(f"Quality score:   {score_pct:.1f}%")


def _print_chinese(result: dict[str, object]) -> None:
    labels = CLI_STRINGS_ZH
    score_pct = float(result["quality_score"]) * 100
    print(labels["success"])
    print()
    print(f"{labels['input_rows']}:      {result['input_rows']}")
    print(f"{labels['clean_rows']}:      {result['clean_rows']}")
    print(f"{labels['rejected_rows']}:      {result['rejected_rows']}")
    print(f"{labels['quality_score']}:    {score_pct:.1f}%")


def _print_mapping(result: dict[str, object], *, chinese: bool) -> None:
    report = result.get("column_mapping")
    if not isinstance(report, dict):
        return
    renames = report.get("renames") or {}
    unmapped = report.get("unmapped_columns") or []
    combined = bool(report.get("debit_credit_combined"))
    if not renames and not unmapped and not combined:
        return
    labels = CLI_STRINGS_ZH
    print()
    if renames:
        print(labels["mapping_header"] if chinese else "Column mapping:")
        applied = {
            item["source"]: item.get("method", "")
            for item in report.get("applied", [])
            if isinstance(item, dict)
        }
        for source, target in renames.items():
            method = applied.get(source, "")
            suffix = f" ({method})" if method else ""
            print(f"- {source} → {target}{suffix}")
    elif chinese:
        print(labels["mapping_none"])
    if unmapped:
        header = labels["unmapped"] if chinese else "Unmapped columns kept"
        print(f"{header}: {', '.join(str(column) for column in unmapped)}")
    if combined:
        print(
            labels["debit_credit"]
            if chinese
            else "Debit/credit columns were combined into amount "
            "(withdrawals negative, deposits positive). Original columns were kept."
        )


def _print_outputs(result: dict[str, object], *, chinese: bool) -> None:
    print()
    print(CLI_STRINGS_ZH["outputs"] if chinese else "Outputs:")
    for path in result["outputs"]:  # type: ignore[index]
        file_path = Path(str(path))
        try:
            display = file_path.resolve().relative_to(Path.cwd().resolve()).as_posix()
        except ValueError:
            display = file_path.name
        print(f"- {display}")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args_list = list(sys.argv[1:] if argv is None else argv)
    try:
        args = parser.parse_args(args_list)
    except SystemExit as exc:
        code = exc.code
        if code is None:
            return 0
        return int(code)

    try:
        language = normalize_language(args.language)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    try:
        result = run_pipeline(
            args.input,
            output_dir=args.output_dir,
            evidence_path=args.evidence,
            mapping_path=args.mapping,
            language=language,
        )
    except Exception as exc:
        print(f"Pipeline failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    chinese = language == "zh-TW"
    if chinese:
        _print_chinese(result)
    else:
        _print_english(result)
    _print_mapping(result, chinese=chinese)
    _print_outputs(result, chinese=chinese)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
