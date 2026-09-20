"""Cleaning transforms that quarantine invalid rows instead of hiding them."""

from __future__ import annotations

import pandas as pd

from financial_data_automation.validation import REQUIRED_COLUMNS


def _normalize_strings(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in out.select_dtypes(include=["object", "string"]).columns:
        out[col] = out[col].map(
            lambda v: v.strip() if isinstance(v, str) else v
        )
    return out


def clean_data(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Clean a validated/coerced transaction frame.

    Returns
    -------
    cleaned_df, rejected_df
        Rejected rows include a ``reject_reason`` column.
    """
    working = _normalize_strings(df.copy())
    rejected_parts: list[pd.DataFrame] = []

    # Exact duplicate rows (before uniqueness logic)
    exact_dup_mask = working.duplicated(keep="first")
    if exact_dup_mask.any():
        part = working.loc[exact_dup_mask].copy()
        part["reject_reason"] = "exact_duplicate_row"
        rejected_parts.append(part)
        working = working.loc[~exact_dup_mask].copy()

    for col in REQUIRED_COLUMNS:
        if col not in working.columns:
            part = working.copy()
            part["reject_reason"] = f"missing_column_{col}"
            rejected_parts.append(part)
            empty_clean = working.iloc[0:0].copy()
            rejected = (
                pd.concat(rejected_parts, ignore_index=True)
                if rejected_parts
                else empty_clean.assign(reject_reason=pd.Series(dtype="object"))
            )
            return empty_clean, rejected

    missing_id = working["transaction_id"].isna() | (
        working["transaction_id"].astype(str).str.strip() == ""
    )
    if missing_id.any():
        part = working.loc[missing_id].copy()
        part["reject_reason"] = "missing_transaction_id"
        rejected_parts.append(part)
        working = working.loc[~missing_id].copy()

    invalid_date = working["date"].isna()
    if invalid_date.any():
        part = working.loc[invalid_date].copy()
        part["reject_reason"] = "invalid_date"
        rejected_parts.append(part)
        working = working.loc[~invalid_date].copy()

    invalid_amount = working["amount"].isna()
    if invalid_amount.any():
        part = working.loc[invalid_amount].copy()
        part["reject_reason"] = "invalid_amount"
        rejected_parts.append(part)
        working = working.loc[~invalid_amount].copy()

    missing_description = working["description"].isna() | (
        working["description"].astype(str).str.strip() == ""
    )
    if missing_description.any():
        part = working.loc[missing_description].copy()
        part["reject_reason"] = "missing_description"
        rejected_parts.append(part)
        working = working.loc[~missing_description].copy()

    # Duplicate transaction_id: keep first, reject rest
    dup_id = working["transaction_id"].duplicated(keep="first")
    if dup_id.any():
        part = working.loc[dup_id].copy()
        part["reject_reason"] = "duplicate_transaction_id"
        rejected_parts.append(part)
        working = working.loc[~dup_id].copy()

    for col in ("quantity", "unit_price", "cost"):
        if col in working.columns:
            bad = working[col].notna() & (working[col] < 0)
            if bad.any():
                part = working.loc[bad].copy()
                part["reject_reason"] = f"negative_{col}"
                rejected_parts.append(part)
                working = working.loc[~bad].copy()

    if rejected_parts:
        rejected = pd.concat(rejected_parts, ignore_index=True)
    else:
        rejected = working.iloc[0:0].copy()
        rejected["reject_reason"] = pd.Series(dtype="object")

    cleaned = working.reset_index(drop=True)
    return cleaned, rejected
