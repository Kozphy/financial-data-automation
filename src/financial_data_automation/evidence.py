"""Append-only JSONL audit evidence for pipeline runs."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def new_run_id() -> str:
    """Create a unique run identifier."""
    return uuid.uuid4().hex


def sanitize_input_name(path: str | Path) -> str:
    """Store only the file name in evidence, never absolute user paths."""
    return Path(path).name


def append_evidence(record: dict[str, Any], evidence_path: str | Path) -> Path:
    """
    Append one JSON object as a line to the evidence file.

    Creates parent directories as needed. Append-only from the app's perspective.
    """
    path = Path(evidence_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(record, ensure_ascii=True, sort_keys=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")
    return path


def build_success_evidence(
    *,
    run_id: str,
    input_file: str | Path,
    input_rows: int,
    clean_rows: int,
    rejected_rows: int,
    duplicates_removed: int,
    invalid_dates: int,
    invalid_amounts: int,
    quality_score: float,
    outputs: list[str],
) -> dict[str, Any]:
    """Build a success audit record."""
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "run_id": run_id,
        "input_file": sanitize_input_name(input_file),
        "input_rows": input_rows,
        "clean_rows": clean_rows,
        "rejected_rows": rejected_rows,
        "duplicates_removed": duplicates_removed,
        "invalid_dates": invalid_dates,
        "invalid_amounts": invalid_amounts,
        "quality_score": quality_score,
        "outputs": outputs,
        "status": "success",
    }


def build_failure_evidence(
    *,
    run_id: str,
    input_file: str | Path | None,
    error: BaseException,
) -> dict[str, Any]:
    """Build a failure audit record without sensitive path details."""
    record: dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "run_id": run_id,
        "status": "failed",
        "error_type": type(error).__name__,
        "error_message": str(error),
    }
    if input_file is not None:
        record["input_file"] = sanitize_input_name(input_file)
    return record
