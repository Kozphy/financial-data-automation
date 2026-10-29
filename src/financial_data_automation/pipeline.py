"""End-to-end orchestration for the financial data pipeline."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from financial_data_automation.analytics import (
    compute_financial_summary,
    compute_monthly_totals,
    compute_quality_score,
)
from financial_data_automation.cleaning import clean_data
from financial_data_automation.evidence import (
    append_evidence,
    build_failure_evidence,
    build_success_evidence,
    new_run_id,
)
from financial_data_automation.i18n import normalize_language
from financial_data_automation.ingestion import load_data
from financial_data_automation.mapping import map_columns
from financial_data_automation.reporting import verify_outputs, write_reports
from financial_data_automation.validation import validate_schema


def _project_root() -> Path:
    # src/financial_data_automation/pipeline.py -> repo root
    return Path(__file__).resolve().parents[2]


def run_pipeline(
    input_path: str | Path,
    *,
    output_dir: str | Path | None = None,
    evidence_path: str | Path | None = None,
    mapping_path: str | Path | None = None,
    language: str = "en",
) -> dict[str, Any]:
    """
    Execute load → map columns → validate → clean → analyze → report → verify → evidence.

    Parameters
    ----------
    input_path:
        CSV or XLSX input file.
    output_dir:
        Destination for processed artifacts. Defaults to ``data/processed``.
    evidence_path:
        JSONL audit log path. Defaults to ``evidence/audit.jsonl``.
    mapping_path:
        Optional CSV, JSON, or XLSX file mapping source headers to canonical
        fields (columns ``source`` and ``target``).
    language:
        Report label language. ``en`` (default) or ``zh-TW``.
    """
    root = _project_root()
    out_dir = Path(output_dir) if output_dir is not None else root / "data" / "processed"
    evidence_file = (
        Path(evidence_path) if evidence_path is not None else root / "evidence" / "audit.jsonl"
    )
    run_id = new_run_id()
    lang = normalize_language(language)

    try:
        raw = load_data(input_path)
        input_rows = int(len(raw))
        raw, mapping_report = map_columns(raw, mapping_path)

        validation = validate_schema(raw)
        if validation["missing_columns"]:
            present = ", ".join(str(column) for column in raw.columns) or "(none)"
            raise ValueError(
                "Missing required columns: "
                + ", ".join(validation["missing_columns"])
                + f". Present columns: {present}."
            )

        coerced = validation["coerced_frame"]
        cleaned, rejected = clean_data(coerced)

        # Quarantined duplicates: exact row copies and later duplicate transaction_ids.
        duplicate_reasons = {"exact_duplicate_row", "duplicate_transaction_id"}
        duplicates_removed = (
            int(rejected["reject_reason"].isin(duplicate_reasons).sum())
            if not rejected.empty
            else 0
        )

        summary = compute_financial_summary(cleaned)
        monthly = compute_monthly_totals(cleaned)
        quality_score = compute_quality_score(input_rows, int(len(cleaned)))

        quality_rows = [
            {"check": "missing_columns", "value": len(validation["missing_columns"])},
            {"check": "invalid_dates", "value": validation["invalid_dates"]},
            {"check": "invalid_amounts", "value": validation["invalid_amounts"]},
            {
                "check": "duplicate_transaction_ids_flagged",
                "value": validation["duplicate_transaction_ids"],
            },
            {"check": "rejected_rows", "value": int(len(rejected))},
            {"check": "clean_rows", "value": int(len(cleaned))},
            {"check": "quality_score", "value": quality_score},
            {
                "check": "inconsistent_quantity_price",
                "value": validation.get("inconsistent_quantity_price", 0),
            },
            {"check": "columns_mapped", "value": len(mapping_report["renames"])},
            {
                "check": "debit_credit_combined",
                "value": int(bool(mapping_report["debit_credit_combined"])),
            },
        ]

        outputs = write_reports(
            cleaned_df=cleaned,
            rejected_df=rejected,
            summary=summary,
            monthly_df=monthly,
            quality_rows=quality_rows,
            output_dir=out_dir,
            language=lang,
        )
        missing = verify_outputs(out_dir, outputs)
        if missing:
            raise RuntimeError(f"Missing expected outputs: {', '.join(missing)}")

        evidence = build_success_evidence(
            run_id=run_id,
            input_file=input_path,
            input_rows=input_rows,
            clean_rows=int(len(cleaned)),
            rejected_rows=int(len(rejected)),
            duplicates_removed=duplicates_removed,
            invalid_dates=int(validation["invalid_dates"]),
            invalid_amounts=int(validation["invalid_amounts"]),
            quality_score=quality_score,
            outputs=outputs,
            language=lang,
            columns_mapped=len(mapping_report["renames"]),
            debit_credit_combined=bool(mapping_report["debit_credit_combined"]),
            mapping_file=str(mapping_path) if mapping_path else None,
        )
        append_evidence(evidence, evidence_file)

        return {
            "status": "success",
            "run_id": run_id,
            "input_rows": input_rows,
            "clean_rows": int(len(cleaned)),
            "rejected_rows": int(len(rejected)),
            "quality_score": quality_score,
            "summary": summary,
            "outputs": [str(out_dir / name) for name in outputs],
            "output_names": outputs,
            "validation": {
                k: v for k, v in validation.items() if k != "coerced_frame"
            },
            "column_mapping": mapping_report,
            "language": lang,
        }
    except Exception as exc:
        failure = build_failure_evidence(
            run_id=run_id,
            input_file=input_path,
            error=exc,
        )
        append_evidence(failure, evidence_file)
        raise
