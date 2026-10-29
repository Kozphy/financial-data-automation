#!/usr/bin/env python3
"""Local web UI for the financial data cleaning pipeline.

Run from the repository root:

    python -m pip install -r requirements-ui.txt
    streamlit run streamlit_app.py
"""

from __future__ import annotations

import sys
import tempfile
from io import BytesIO
from pathlib import Path

_SRC = Path(__file__).resolve().parent / "src"
if _SRC.is_dir() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import pandas as pd
import streamlit as st

from financial_data_automation.i18n import normalize_language
from financial_data_automation.pipeline import run_pipeline

_ROOT = Path(__file__).resolve().parent

_COPY: dict[str, dict[str, str]] = {
    "en": {
        "page_title": "Financial data cleaning",
        "title": "Financial data cleaning",
        "subtitle": (
            "Upload a bank, QuickBooks, or Shopee export. "
            "The pipeline maps the columns, quarantines bad rows, and prepares the reports."
        ),
        "language": "Language",
        "english": "English",
        "chinese": "繁體中文",
        "data_file": "Transaction file (.csv or .xlsx)",
        "mapping_file": "Column mapping file (optional)",
        "mapping_help": "CSV, JSON, or Excel with columns source and target.",
        "template": "Download a mapping template",
        "run": "Clean this file",
        "need_file": "Choose a CSV or Excel file first.",
        "bad_type": "Use a .csv or .xlsx file.",
        "input_rows": "Input rows",
        "clean_rows": "Clean rows",
        "rejected_rows": "Rejected rows",
        "quality": "Quality score",
        "mapping_header": "Column mapping",
        "unmapped": "Kept as-is",
        "debit_credit": (
            "Withdrawals were stored as negative amounts and deposits as positive amounts. "
            "The original debit and credit columns are still in the file."
        ),
        "tab_clean": "Cleaned data",
        "tab_rejected": "Rejected rows",
        "tab_summary": "Financial summary",
        "tab_quality": "Quality report",
        "download_clean": "Download cleaned data",
        "download_rejected": "Download rejected rows",
        "download_summary": "Download financial summary",
        "download_quality": "Download quality report",
        "empty_reject": "No rows were rejected.",
        "failed": "The file could not be cleaned.",
        "reason": "Reject reason",
    },
    "zh-TW": {
        "page_title": "財務資料清理",
        "title": "財務資料清理",
        "subtitle": (
            "上傳銀行對帳單、QuickBooks 或蝦皮後台匯出的 Excel／CSV。"
            "系統會對應欄位、隔離有問題的列，並產生可下載的報表。不會偷偷刪除任何資料。"
        ),
        "language": "語言",
        "english": "English",
        "chinese": "繁體中文",
        "data_file": "交易檔（.csv 或 .xlsx）",
        "mapping_file": "欄位對應檔（選填）",
        "mapping_help": "CSV、JSON 或 Excel，欄位為 source 與 target（來源與目標）。",
        "template": "下載欄位對應範本",
        "run": "開始清理",
        "need_file": "請先選擇 CSV 或 Excel 檔。",
        "bad_type": "請使用 .csv 或 .xlsx 檔。",
        "input_rows": "輸入列數",
        "clean_rows": "有效列數",
        "rejected_rows": "剔除列數",
        "quality": "品質分數",
        "mapping_header": "欄位對應",
        "unmapped": "未對應、原樣保留",
        "debit_credit": "支出已轉成負數、存入維持正數，並寫入金額欄。原始支出／存入欄仍保留。",
        "tab_clean": "清理後資料",
        "tab_rejected": "剔除列",
        "tab_summary": "財務摘要",
        "tab_quality": "品質報告",
        "download_clean": "下載清理後資料",
        "download_rejected": "下載剔除列",
        "download_summary": "下載財務摘要",
        "download_quality": "下載品質報告",
        "empty_reject": "沒有列被剔除。",
        "failed": "這個檔案無法完成清理。",
        "reason": "剔除原因",
    },
}

_TEMPLATE = (
    "source,target\n"
    "訂單編號,transaction_id\n"
    "交易日期,date\n"
    "摘要,description\n"
    "金額,amount\n"
    "支出,debit\n"
    "存入,credit\n"
).encode("utf-8")

_OUTPUTS = {
    "cleaned_data.xlsx": "download_clean",
    "rejected_rows.xlsx": "download_rejected",
    "financial_summary.xlsx": "download_summary",
    "quality_report.csv": "download_quality",
}


def _show_mapping(report: dict[str, object], text: dict[str, str]) -> None:
    renames = report.get("renames") or {}
    unmapped = report.get("unmapped_columns") or []
    applied = {
        item["source"]: item.get("method", "")
        for item in report.get("applied", [])
        if isinstance(item, dict)
    }
    if isinstance(renames, dict) and renames:
        rows = [
            {"source": source, "target": target, "method": applied.get(source, "")}
            for source, target in renames.items()
        ]
        st.markdown(f"**{text['mapping_header']}**")
        st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
    if unmapped:
        st.caption(f"{text['unmapped']}: {', '.join(str(column) for column in unmapped)}")
    if report.get("debit_credit_combined"):
        st.info(text["debit_credit"])


def main() -> None:
    st.set_page_config(page_title="Financial data cleaning / 財務資料清理", page_icon="📒", layout="wide")
    language_code = st.radio(
        "Language / 語言",
        options=["en", "zh-TW"],
        format_func=lambda code: "English" if code == "en" else "繁體中文",
        horizontal=True,
    )
    language = normalize_language(str(language_code))
    text = _COPY[language]

    st.title(text["title"])
    st.write(text["subtitle"])

    data_col, map_col = st.columns(2)
    with data_col:
        data_file = st.file_uploader(text["data_file"], type=["csv", "xlsx"], key="data_file")
    with map_col:
        mapping_file = st.file_uploader(
            text["mapping_file"],
            type=["csv", "json", "xlsx"],
            help=text["mapping_help"],
            key="mapping_file",
        )
        st.download_button(text["template"], data=_TEMPLATE, file_name="column_mapping.csv", mime="text/csv")

    if st.button(text["run"], type="primary", key="run_clean"):
        if data_file is None:
            st.session_state.pop("clean_result", None)
            st.warning(text["need_file"])
        else:
            suffix = Path(data_file.name).suffix.lower()
            if suffix not in {".csv", ".xlsx"}:
                st.session_state.pop("clean_result", None)
                st.error(text["bad_type"])
            else:
                st.session_state["clean_result"] = _run_upload(data_file, mapping_file, language)

    stored = st.session_state.get("clean_result")
    if not isinstance(stored, dict):
        return
    if stored.get("language") != language and stored.get("data_bytes"):
        stored = _execute(
            data_bytes=stored["data_bytes"],  # type: ignore[arg-type]
            data_suffix=str(stored["data_suffix"]),
            mapping_bytes=stored.get("mapping_bytes"),  # type: ignore[arg-type]
            mapping_suffix=stored.get("mapping_suffix"),  # type: ignore[arg-type]
            language=language,
        )
        st.session_state["clean_result"] = stored
    if stored.get("error"):
        st.error(f"{text['failed']} {stored['error']}")
        return

    _show_result(stored, text)


def _run_upload(data_file: object, mapping_file: object | None, language: str) -> dict[str, object]:
    data_suffix = Path(data_file.name).suffix.lower()  # type: ignore[attr-defined]
    mapping_bytes = None
    mapping_suffix = None
    if mapping_file is not None:
        mapping_bytes = mapping_file.getvalue()  # type: ignore[attr-defined]
        mapping_suffix = Path(mapping_file.name).suffix.lower()  # type: ignore[attr-defined]
    return _execute(
        data_bytes=data_file.getvalue(),  # type: ignore[attr-defined]
        data_suffix=data_suffix,
        mapping_bytes=mapping_bytes,
        mapping_suffix=mapping_suffix,
        language=language,
    )


def _execute(
    *,
    data_bytes: bytes,
    data_suffix: str,
    mapping_bytes: bytes | None,
    mapping_suffix: str | None,
    language: str,
) -> dict[str, object]:
    data_path = _write_bytes(data_bytes, data_suffix)
    mapping_path: Path | None = None
    if mapping_bytes is not None and mapping_suffix:
        mapping_path = _write_bytes(mapping_bytes, mapping_suffix)
    base = {
        "language": language,
        "data_bytes": data_bytes,
        "data_suffix": data_suffix,
        "mapping_bytes": mapping_bytes,
        "mapping_suffix": mapping_suffix,
    }
    try:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "processed"
            try:
                result = run_pipeline(
                    data_path,
                    output_dir=output_dir,
                    evidence_path=_ROOT / "evidence" / "audit.jsonl",
                    mapping_path=mapping_path,
                    language=language,
                )
            except Exception as exc:
                return {**base, "error": f"{type(exc).__name__}: {exc}"}
            files = {name: (output_dir / name).read_bytes() for name in _OUTPUTS}
            return {
                **base,
                "error": None,
                "input_rows": result["input_rows"],
                "clean_rows": result["clean_rows"],
                "rejected_rows": result["rejected_rows"],
                "quality_score": result["quality_score"],
                "mapping": result.get("column_mapping"),
                "files": files,
            }
    finally:
        data_path.unlink(missing_ok=True)
        if mapping_path is not None:
            mapping_path.unlink(missing_ok=True)


def _write_bytes(payload: bytes, suffix: str) -> Path:
    handle = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    handle.write(payload)
    handle.close()
    return Path(handle.name)


def _show_result(stored: dict[str, object], text: dict[str, str]) -> None:
    score = float(stored["quality_score"]) * 100  # type: ignore[arg-type]
    metric_cols = st.columns(4)
    metric_cols[0].metric(text["input_rows"], stored["input_rows"])
    metric_cols[1].metric(text["clean_rows"], stored["clean_rows"])
    metric_cols[2].metric(text["rejected_rows"], stored["rejected_rows"])
    metric_cols[3].metric(text["quality"], f"{score:.1f}%")

    mapping = stored.get("mapping")
    if isinstance(mapping, dict):
        _show_mapping(mapping, text)

    files = stored["files"]
    if not isinstance(files, dict):
        return
    cleaned = pd.read_excel(BytesIO(files["cleaned_data.xlsx"]))
    rejected = pd.read_excel(BytesIO(files["rejected_rows.xlsx"]))
    summary = pd.read_excel(BytesIO(files["financial_summary.xlsx"]), sheet_name=0)
    monthly = pd.read_excel(BytesIO(files["financial_summary.xlsx"]), sheet_name=1)
    quality = pd.read_csv(BytesIO(files["quality_report.csv"]))

    tab_clean, tab_rejected, tab_summary, tab_quality = st.tabs(
        [text["tab_clean"], text["tab_rejected"], text["tab_summary"], text["tab_quality"]]
    )
    with tab_clean:
        st.dataframe(cleaned, hide_index=True, width="stretch")
    with tab_rejected:
        if rejected.empty:
            st.success(text["empty_reject"])
        else:
            st.dataframe(rejected, hide_index=True, width="stretch")
    with tab_summary:
        st.dataframe(summary, hide_index=True, width="stretch")
        st.dataframe(monthly, hide_index=True, width="stretch")
    with tab_quality:
        st.dataframe(quality, hide_index=True, width="stretch")

    download_cols = st.columns(4)
    for column, (name, label_key) in zip(download_cols, _OUTPUTS.items(), strict=True):
        mime = (
            "text/csv"
            if name.endswith(".csv")
            else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        column.download_button(
            text[label_key],
            data=files[name],
            file_name=name,
            mime=mime,
            key=f"download-{name}-{stored.get('language')}",
        )


main()
