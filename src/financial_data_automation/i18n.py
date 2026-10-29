"""Report and CLI labels in English and Traditional Chinese (zh-TW)."""

from __future__ import annotations

from typing import Literal, Never

import pandas as pd

Language = Literal["en", "zh-TW"]

SUPPORTED_LANGUAGES: tuple[Language, ...] = ("en", "zh-TW")

COLUMN_LABELS_ZH: dict[str, str] = {
    "transaction_id": "交易編號",
    "date": "日期",
    "description": "摘要",
    "amount": "金額",
    "customer": "客戶",
    "category": "類別",
    "currency": "幣別",
    "cost": "成本",
    "quantity": "數量",
    "unit_price": "單價",
    "region": "地區",
    "debit": "支出",
    "credit": "存入",
    "reject_reason": "剔除原因",
    "reject_reason_label": "剔除說明",
    "month": "月份",
    "total_amount": "合計金額",
    "record_count": "筆數",
    "average_amount": "平均金額",
    "minimum_amount": "最低金額",
    "maximum_amount": "最高金額",
    "gross_profit": "毛利",
    "gross_margin": "毛利率",
    "check": "檢查項目",
    "value": "數值",
    "label": "說明",
}

CHECK_LABELS_EN: dict[str, str] = {
    "missing_columns": "Missing columns",
    "invalid_dates": "Invalid dates",
    "invalid_amounts": "Invalid amounts",
    "duplicate_transaction_ids_flagged": "Duplicate transaction IDs",
    "rejected_rows": "Rejected rows",
    "clean_rows": "Clean rows",
    "quality_score": "Quality score",
    "inconsistent_quantity_price": "Quantity × unit price ≠ amount",
    "columns_mapped": "Columns mapped",
    "debit_credit_combined": "Debit and credit combined into amount",
}

CHECK_LABELS_ZH: dict[str, str] = {
    "missing_columns": "缺少欄位",
    "invalid_dates": "無效日期",
    "invalid_amounts": "無效金額",
    "duplicate_transaction_ids_flagged": "重複交易編號",
    "rejected_rows": "剔除列數",
    "clean_rows": "有效列數",
    "quality_score": "品質分數",
    "inconsistent_quantity_price": "數量乘單價與金額不符",
    "columns_mapped": "已對應欄位數",
    "debit_credit_combined": "已將支出與存入合併為金額",
}

REJECT_LABELS_ZH: dict[str, str] = {
    "exact_duplicate_row": "完全重複列",
    "duplicate_transaction_id": "交易編號重複",
    "invalid_date": "日期無效",
    "invalid_amount": "金額無效",
    "missing_description": "缺少摘要",
    "missing_transaction_id": "缺少交易編號",
    "negative_quantity": "數量為負數",
    "negative_unit_price": "單價為負數",
    "negative_cost": "成本為負數",
    "missing_column_transaction_id": "缺少交易編號欄",
    "missing_column_date": "缺少日期欄",
    "missing_column_description": "缺少摘要欄",
    "missing_column_amount": "缺少金額欄",
}

SHEET_LABELS_ZH: dict[str, str] = {
    "summary": "摘要",
    "monthly": "每月合計",
    "quality": "品質",
}

CLI_STRINGS_ZH: dict[str, str] = {
    "success": "清理完成。",
    "input_rows": "輸入列數",
    "clean_rows": "有效列數",
    "rejected_rows": "剔除列數",
    "quality_score": "品質分數",
    "outputs": "輸出檔案：",
    "mapping_header": "欄位對應：",
    "mapping_none": "欄位名稱已符合標準格式。",
    "unmapped": "未對應、原樣保留的欄位",
    "debit_credit": "已把支出（負）與存入（正）合併成金額欄，原始欄位仍保留。",
}


def normalize_language(language: str) -> Language:
    """Accept ``en`` and ``zh-TW`` (plus a few common spellings)."""
    key = language.strip().replace("_", "-").lower()
    if key in {"en", "english"}:
        return "en"
    if key in {"zh-tw", "zh-hant", "zh-hant-tw", "traditional-chinese"}:
        return "zh-TW"
    supported = ", ".join(SUPPORTED_LANGUAGES)
    raise ValueError(
        f"Unsupported language '{language}'. Supported languages: {supported}"
    )


def _assert_never(value: Never) -> Never:
    raise AssertionError(f"unsupported language: {value}")


def check_label(check: str, language: Language) -> str:
    """Human label for a quality-check id."""
    if language == "en":
        return CHECK_LABELS_EN.get(check, check)
    if language == "zh-TW":
        return CHECK_LABELS_ZH.get(check, check)
    return _assert_never(language)


def localize_frame(df: pd.DataFrame, language: Language) -> pd.DataFrame:
    """Copy ``df`` with Traditional Chinese headers. English headers stay as-is."""
    if language == "en":
        return df.copy()
    if language == "zh-TW":
        rename = {column: COLUMN_LABELS_ZH[column] for column in df.columns if column in COLUMN_LABELS_ZH}
        return df.rename(columns=rename)
    return _assert_never(language)


def sheet_names(language: Language) -> tuple[str, str, str]:
    """Excel sheet names for the financial summary workbook."""
    if language == "en":
        return "summary", "monthly", "quality"
    if language == "zh-TW":
        return SHEET_LABELS_ZH["summary"], SHEET_LABELS_ZH["monthly"], SHEET_LABELS_ZH["quality"]
    return _assert_never(language)


def reject_label(reason: object, language: Language) -> str:
    """Human label for a reject-reason code. English returns the code itself."""
    text = "" if reason is None else str(reason)
    if language == "en":
        return text
    if language == "zh-TW":
        return REJECT_LABELS_ZH.get(text, text)
    return _assert_never(language)
