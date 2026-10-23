"""Command-line entry for one input file."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from financial_data_automation.pipeline import run_pipeline


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="financial-data-automation",
        description="Validate a transaction file and write an Excel summary.",
    )
    parser.add_argument("input", type=Path, help="CSV or XLSX transaction file")
    parser.add_argument("--output", type=Path, help="Directory for the Excel and CSV reports")
    parser.add_argument("--evidence", type=Path, help="JSONL evidence path")
    args = parser.parse_args(argv)
    try:
        result = run_pipeline(
            args.input,
            output_dir=args.output,
            evidence_path=args.evidence,
        )
    except Exception as exc:
        print(f"Pipeline failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    print("Pipeline completed successfully.")
    print(f"Input rows: {result['input_rows']}")
    print(f"Clean rows: {result['clean_rows']}")
    print(f"Rejected rows: {result['rejected_rows']}")
    print(f"Quality score: {result['quality_score'] * 100:.1f}%")
    for path in result["outputs"]:
        print(f"- {Path(path).name}")
    return 0
