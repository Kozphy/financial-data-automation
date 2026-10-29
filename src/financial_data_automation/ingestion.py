"""Load Excel/CSV financial datasets and normalize column names."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

# Input contract: CSV and XLSX only. Legacy .xls needs a different engine and is not supported.
SUPPORTED_SUFFIXES = {".csv", ".xlsx"}


def normalize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize column names to lowercase snake_case."""
    out = df.copy()
    out.columns = [
        str(col).strip().lower().replace(" ", "_")
        for col in out.columns
    ]
    return out


def load_data(path: str | Path) -> pd.DataFrame:
    """
    Load a CSV or Excel file into a DataFrame.

    Raises
    ------
    FileNotFoundError
        If the path does not exist.
    ValueError
        If the file extension is unsupported.
    """
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"Input file not found: {file_path.name}")

    suffix = file_path.suffix.lower()
    if suffix not in SUPPORTED_SUFFIXES:
        raise ValueError(
            f"Unsupported file format '{suffix}'. "
            f"Supported formats: {', '.join(sorted(SUPPORTED_SUFFIXES))}"
        )

    if suffix == ".csv":
        df = _read_csv(file_path)
    else:
        df = pd.read_excel(file_path, engine="openpyxl")

    return normalize_column_names(df)


def _read_csv(file_path: Path) -> pd.DataFrame:
    """Read CSV as UTF-8 (with BOM), UTF-16, or Big5/cp950."""
    raw = file_path.read_bytes()[:4]
    if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
        return pd.read_csv(file_path, encoding="utf-16")

    last_error: UnicodeDecodeError | None = None
    for encoding in ("utf-8-sig", "cp950"):
        try:
            return pd.read_csv(file_path, encoding=encoding)
        except UnicodeDecodeError as exc:
            last_error = exc
    raise ValueError(
        f"Could not decode '{file_path.name}' as UTF-8 or Big5 (cp950). "
        "Save the file as UTF-8 and try again."
    ) from last_error
