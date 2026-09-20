#!/usr/bin/env python3
"""CLI entry point for the financial data automation pipeline."""

from __future__ import annotations

import sys
from pathlib import Path

# Allow `python run_pipeline.py ...` after `pip install -r requirements.txt`
# without requiring an editable package install.
_SRC = Path(__file__).resolve().parent / "src"
if _SRC.is_dir() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from financial_data_automation.pipeline import run_pipeline


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args:
        print("Usage: python run_pipeline.py <input.csv|input.xlsx>", file=sys.stderr)
        return 2

    input_path = Path(args[0])
    try:
        result = run_pipeline(input_path)
    except Exception as exc:
        print(f"Pipeline failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    score_pct = result["quality_score"] * 100
    print("Pipeline completed successfully.")
    print()
    print(f"Input rows:      {result['input_rows']}")
    print(f"Clean rows:       {result['clean_rows']}")
    print(f"Rejected rows:     {result['rejected_rows']}")
    print(f"Quality score:   {score_pct:.1f}%")
    print()
    print("Outputs:")
    for path in result["outputs"]:
        # Print path relative to CWD when possible (no home-directory leakage intent)
        try:
            display = Path(path).resolve().relative_to(Path.cwd().resolve())
        except ValueError:
            display = Path(path).name
        print(f"- {display.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
