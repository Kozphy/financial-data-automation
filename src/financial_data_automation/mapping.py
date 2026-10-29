"""Map source export headers onto the canonical transaction schema.

Matching order for each column:

1. Optional user mapping file (CSV, JSON, or XLSX) — always wins
2. Already-canonical header
3. Exact synonym (English, Traditional Chinese, and common Simplified forms)
4. Fuzzy match for non-Chinese headers (typos such as ``ammount``)

Unmapped extra columns are kept. Required fields that stay unmapped, and
required fields claimed by more than one column, raise ``ValueError``.
Bank-style debit/credit (支出/存入) columns are combined into ``amount``
when ``amount`` itself was not mapped: deposits are positive, withdrawals
are negative. The original debit and credit columns are kept.
"""

from __future__ import annotations

import json
import re
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

import pandas as pd

from financial_data_automation.formats import parse_amount_series, to_halfwidth

REQUIRED_COLUMNS: tuple[str, ...] = (
    "transaction_id",
    "date",
    "description",
    "amount",
)
OPTIONAL_COLUMNS: tuple[str, ...] = (
    "customer",
    "category",
    "currency",
    "cost",
    "quantity",
    "unit_price",
    "region",
)
# Not part of the stored schema. Combined into ``amount`` when amount is absent.
SPECIAL_COLUMNS: tuple[str, ...] = ("debit", "credit")

CANONICAL_COLUMNS: tuple[str, ...] = REQUIRED_COLUMNS + OPTIONAL_COLUMNS
MAPPING_TARGETS: frozenset[str] = frozenset(CANONICAL_COLUMNS + SPECIAL_COLUMNS)
# Wrong amount, date, or id would change the books. Description can fall
# through to the next synonym (摘要 before 備註) and keep the extra column.
STRICT_REQUIRED: frozenset[str] = frozenset({"transaction_id", "date", "amount"})

# Higher in each tuple = preferred when an optional field is ambiguous.
# Required-field ties are never guessed; they raise.
_SYNONYM_GROUPS: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "transaction_id",
        (
            "transaction_id",
            "transactionid",
            "txn_id",
            "trans_id",
            "transaction_no",
            "transaction_number",
            "transaction_num",
            "reference",
            "reference_no",
            "reference_number",
            "ref_no",
            "invoice_no",
            "invoice_number",
            "invoice_id",
            "doc_no",
            "document_no",
            "document_number",
            "voucher_no",
            "voucher_number",
            "order_id",
            "order_no",
            "order_number",
            "order_sn",
            "num",
            "id",
            "交易編號",
            "交易序号",
            "交易序號",
            "交易號碼",
            "交易号",
            "單號",
            "单号",
            "序號",
            "序号",
            "訂單編號",
            "订单编号",
            "訂單號碼",
            "订单号",
            "傳票號碼",
            "傳票編號",
            "憑證號碼",
            "憑單編號",
            "發票號碼",
            "发票号码",
        ),
    ),
    (
        "date",
        (
            "date",
            "txn_date",
            "transaction_date",
            "trans_date",
            "posting_date",
            "post_date",
            "value_date",
            "trade_date",
            "order_date",
            "invoice_date",
            "accounting_date",
            "book_date",
            "日期",
            "交易日期",
            "帳務日期",
            "账务日期",
            "入帳日期",
            "入账日期",
            "過帳日期",
            "过账日期",
            "記帳日期",
            "记账日期",
            "訂單日期",
            "订单日期",
            "訂單成立日期",
            "成立日期",
            "發票日期",
            "交易時間",
            "交易时间",
        ),
    ),
    (
        "description",
        (
            "description",
            "desc",
            "memo",
            "narrative",
            "details",
            "detail",
            "particulars",
            "item",
            "item_name",
            "product_name",
            "summary",
            "remarks",
            "remark",
            "note",
            "notes",
            "transaction_description",
            "memo_description",
            "摘要",
            "說明",
            "说明",
            "交易摘要",
            "交易內容",
            "交易内容",
            "品名",
            "商品名稱",
            "商品名称",
            "用途",
            "敘述",
            "叙述",
            "備註",
            "备注",
        ),
    ),
    (
        "amount",
        (
            "amount",
            "amt",
            "transaction_amount",
            "total_amount",
            "net_amount",
            "payment_amount",
            "paid_amount",
            "total",
            "金額",
            "金额",
            "交易金額",
            "交易金额",
            "總金額",
            "总金额",
            "合計",
            "合计",
            "訂單金額",
            "订单金额",
            "成交金額",
            "成交金额",
            "付款金額",
            "付款金额",
            "實付金額",
            "买家总支付金额",
            "買家總支付金額",
            "商品總價",
            "商品总价",
        ),
    ),
    (
        "debit",
        (
            "debit",
            "withdrawal",
            "withdrawals",
            "money_out",
            "paid_out",
            "dr",
            "支出",
            "借方",
            "借方金額",
            "借方金额",
            "提款",
            "轉出",
            "转出",
            "扣款",
        ),
    ),
    (
        "credit",
        (
            "credit",
            "deposit",
            "deposits",
            "money_in",
            "paid_in",
            "cr",
            "存入",
            "貸方",
            "贷方",
            "貸方金額",
            "贷方金额",
            "存款",
            "轉入",
            "转入",
        ),
    ),
    (
        "customer",
        (
            "customer",
            "customer_name",
            "client",
            "client_name",
            "name",
            "payer",
            "payee",
            "buyer",
            "vendor",
            "counterparty",
            "客戶",
            "客户",
            "客戶名稱",
            "客户名称",
            "買方",
            "买方",
            "買家",
            "买家",
            "買家帳號",
            "买家账号",
            "廠商",
            "厂商",
            "交易對象",
            "交易对象",
            "戶名",
            "户名",
        ),
    ),
    (
        "category",
        (
            "category",
            "transaction_type",
            "expense_category",
            "class",
            "split",
            "類別",
            "类别",
            "分類",
            "分类",
            "科目",
            "會計科目",
            "会计科目",
            "交易類型",
            "交易类型",
        ),
    ),
    (
        "currency",
        (
            "currency",
            "currency_code",
            "curr",
            "ccy",
            "幣別",
            "币别",
            "幣種",
            "币种",
            "貨幣",
            "货币",
        ),
    ),
    (
        "cost",
        (
            "cost",
            "cogs",
            "unit_cost",
            "total_cost",
            "成本",
            "銷貨成本",
            "销货成本",
        ),
    ),
    (
        "quantity",
        (
            "quantity",
            "qty",
            "units",
            "數量",
            "数量",
        ),
    ),
    (
        "unit_price",
        (
            "unit_price",
            "price",
            "item_price",
            "單價",
            "单价",
        ),
    ),
    (
        "region",
        (
            "region",
            "area",
            "location",
            "branch",
            "地區",
            "地区",
            "區域",
            "区域",
            "門市",
            "门市",
        ),
    ),
)

_FUZZY_THRESHOLD = 0.88
_FUZZY_MARGIN = 0.04
_SUGGESTION_THRESHOLD = 0.8
_MIN_FUZZY_LENGTH = 6

_SOURCE_HEADERS = frozenset(
    {
        "source",
        "from",
        "column",
        "source_column",
        "header",
        "來源",
        "来源",
        "欄位",
        "栏位",
        "原始欄位",
        "原始栏位",
    }
)
_TARGET_HEADERS = frozenset(
    {
        "target",
        "to",
        "canonical",
        "maps_to",
        "target_column",
        "field",
        "目標",
        "目标",
        "標準欄位",
        "标准栏位",
        "對應",
        "对应",
    }
)


def loose_key(name: object) -> str:
    """Case-fold and strip punctuation so ``Txn. ID`` and ``txn_id`` compare equal."""
    text = to_halfwidth(str(name)).strip().lower()
    text = re.sub(r"\(.*?\)", "", text)
    text = re.sub(r"[^0-9a-z\u4e00-\u9fff]+", "", text)
    return text


def _build_synonym_index() -> dict[str, tuple[str, int]]:
    index: dict[str, tuple[str, int]] = {}
    for target, synonyms in _SYNONYM_GROUPS:
        for priority, synonym in enumerate(synonyms):
            key = loose_key(synonym)
            # First occurrence wins so the table stays unambiguous.
            index.setdefault(key, (target, priority))
    return index


SYNONYM_INDEX: dict[str, tuple[str, int]] = _build_synonym_index()


def _contains_cjk(text: str) -> bool:
    return any("\u4e00" <= ch <= "\u9fff" for ch in text)


def _ratio(left: str, right: str) -> float:
    if not left or not right:
        return 0.0
    return SequenceMatcher(None, left, right).ratio()


def _present_mask(series: pd.Series) -> pd.Series:
    return series.map(
        lambda value: not (
            value is None
            or (isinstance(value, str) and value.strip() == "")
            or (not isinstance(value, str) and pd.isna(value))
        )
    )


def combine_debit_credit(df: pd.DataFrame) -> tuple[pd.DataFrame, bool]:
    """
    Add ``amount`` from debit/credit columns when amount is missing.

    Withdrawals (debit / 支出) reduce the amount. Deposits (credit / 存入)
    increase it. Original columns are retained. A non-numeric debit or credit
    cell is copied through so validation can count it as an invalid amount.
    """
    if "amount" in df.columns:
        return df, False
    has_debit = "debit" in df.columns
    has_credit = "credit" in df.columns
    if not has_debit and not has_credit:
        return df, False

    out = df.copy()
    index = out.index
    if has_debit:
        debit_present = _present_mask(out["debit"])
        debit_num = parse_amount_series(out["debit"])
        debit_bad = debit_present & debit_num.isna()
    else:
        debit_present = pd.Series(False, index=index)
        debit_num = pd.Series(float("nan"), index=index, dtype="float64")
        debit_bad = pd.Series(False, index=index)

    if has_credit:
        credit_present = _present_mask(out["credit"])
        credit_num = parse_amount_series(out["credit"])
        credit_bad = credit_present & credit_num.isna()
    else:
        credit_present = pd.Series(False, index=index)
        credit_num = pd.Series(float("nan"), index=index, dtype="float64")
        credit_bad = pd.Series(False, index=index)

    amount: pd.Series = pd.Series(pd.NA, index=index, dtype="object")
    bad = debit_bad | credit_bad
    if bool(bad.any()):
        # Keep the raw text so downstream validation still sees an invalid amount.
        if has_debit:
            amount.loc[debit_bad] = out.loc[debit_bad, "debit"]
        credit_only_bad = credit_bad & ~debit_bad
        if has_credit and bool(credit_only_bad.any()):
            amount.loc[credit_only_bad] = out.loc[credit_only_bad, "credit"]

    good = ~bad
    neither = ~debit_present & ~credit_present
    net = credit_num.fillna(0) - debit_num.fillna(0)
    usable = good & ~neither
    amount.loc[usable] = net.loc[usable].astype(float)
    out["amount"] = amount
    return out, True


def _read_mapping_frame(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix == ".json":
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
        if isinstance(payload, dict):
            return pd.DataFrame(
                [{"source": key, "target": value} for key, value in payload.items()]
            )
        if isinstance(payload, list):
            return pd.DataFrame(payload)
        raise ValueError(
            f"Mapping file '{path.name}' must be a JSON object or a list of objects."
        )
    if suffix == ".csv":
        last_error: UnicodeDecodeError | None = None
        for encoding in ("utf-8-sig", "cp950"):
            try:
                return pd.read_csv(path, encoding=encoding)
            except UnicodeDecodeError as exc:
                last_error = exc
        raise ValueError(
            f"Could not decode mapping file '{path.name}' as UTF-8 or Big5 (cp950)."
        ) from last_error
    if suffix == ".xlsx":
        return pd.read_excel(path, engine="openpyxl")
    raise ValueError(
        f"Unsupported mapping file format '{suffix}'. "
        "Use .csv, .json, or .xlsx."
    )


def load_user_mapping(path: str | Path) -> dict[str, str]:
    """
    Load a user mapping of source header → canonical field.

    CSV/XLSX files need two columns. Headers may be ``source``/``target``
    (or 來源/目標). A two-column file with other headers is read positionally.
    JSON may be an object ``{"來源欄": "transaction_id"}`` or a list of
    ``{"source", "target"}`` objects.
    """
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"Mapping file not found: {file_path.name}")

    frame = _read_mapping_frame(file_path)
    if frame.empty or len(frame.columns) < 2:
        raise ValueError(
            f"Mapping file '{file_path.name}' needs columns 'source' and 'target'."
        )

    lookup = {loose_key(column): column for column in frame.columns}
    source_col = next((lookup[key] for key in lookup if key in {loose_key(h) for h in _SOURCE_HEADERS}), None)
    target_col = next((lookup[key] for key in lookup if key in {loose_key(h) for h in _TARGET_HEADERS}), None)
    if source_col is None or target_col is None:
        source_col = frame.columns[0]
        target_col = frame.columns[1]

    mapping: dict[str, str] = {}
    for raw_source, raw_target in zip(frame[source_col].tolist(), frame[target_col].tolist(), strict=False):
        if pd.isna(raw_source) or pd.isna(raw_target):
            continue
        source = loose_key(raw_source)
        target = str(raw_target).strip()
        if source == "" or target == "":
            continue
        canonical_target = _canonical_target_name(target)
        if canonical_target not in MAPPING_TARGETS:
            allowed = ", ".join(CANONICAL_COLUMNS + SPECIAL_COLUMNS)
            raise ValueError(
                f"Mapping target '{target}' is not a canonical field. Allowed targets: {allowed}."
            )
        if source in mapping and mapping[source] != canonical_target:
            raise ValueError(
                f"Mapping file maps '{raw_source}' to both "
                f"'{mapping[source]}' and '{canonical_target}'."
            )
        mapping[source] = canonical_target
    if not mapping:
        raise ValueError(f"Mapping file '{file_path.name}' has no source/target rows.")
    return mapping


def _canonical_target_name(target: str) -> str:
    key = loose_key(target)
    if key in {loose_key(name) for name in MAPPING_TARGETS}:
        for name in CANONICAL_COLUMNS + SPECIAL_COLUMNS:
            if loose_key(name) == key:
                return name
    # Allow Chinese labels used as targets ("金額" → amount) via the synonym table.
    found = SYNONYM_INDEX.get(key)
    if found is not None:
        return found[0]
    return target.strip().lower().replace(" ", "_")


def _fuzzy_target(key: str) -> tuple[str, float, float] | None:
    """Return (target, best_score, runner_up_score) for a non-CJK key, or None."""
    if _contains_cjk(key) or len(key) < _MIN_FUZZY_LENGTH:
        return None
    best_target = ""
    best_score = 0.0
    second_score = 0.0
    second_target = ""
    seen: set[tuple[str, str]] = set()
    candidates: list[tuple[str, str]] = [(loose_key(name), name) for name in MAPPING_TARGETS]
    for synonym_key, (target, _priority) in SYNONYM_INDEX.items():
        candidates.append((synonym_key, target))
    for candidate_key, target in candidates:
        marker = (candidate_key, target)
        if marker in seen or not candidate_key or _contains_cjk(candidate_key):
            continue
        seen.add(marker)
        score = _ratio(key, candidate_key)
        if score > best_score:
            second_score = best_score
            second_target = best_target
            best_score = score
            best_target = target
        elif score > second_score and target != best_target:
            second_score = score
            second_target = target
    if best_target == "":
        return None
    if second_target == best_target:
        second_score = 0.0
    return best_target, best_score, second_score


def _suggestions(columns: list[str], missing: list[str], claimed: set[str]) -> list[str]:
    notes: list[str] = []
    remaining = [column for column in columns if column not in claimed]
    for target in missing:
        target_key = loose_key(target)
        best_column = ""
        best_score = 0.0
        for column in remaining:
            key = loose_key(column)
            if _contains_cjk(key):
                continue
            score = _ratio(key, target_key)
            for synonym_key, (synonym_target, _priority) in SYNONYM_INDEX.items():
                if synonym_target != target or _contains_cjk(synonym_key):
                    continue
                score = max(score, _ratio(key, synonym_key))
            if score > best_score:
                best_score = score
                best_column = column
        if best_column and _SUGGESTION_THRESHOLD <= best_score < _FUZZY_THRESHOLD:
            notes.append(
                f"Column '{best_column}' looks like '{target}' "
                f"(similarity {best_score:.2f}) but was not mapped automatically."
            )
    return notes


def build_mapping_error(
    *,
    missing: list[str],
    present: list[str],
    ambiguous: dict[str, list[str]],
    suggestions: list[str],
) -> str:
    """Error text for required columns that could not be mapped."""
    missing_text = ", ".join(missing) if missing else ", ".join(ambiguous)
    present_text = ", ".join(str(column) for column in present) if present else "(none)"
    sentences = [
        f"Missing required columns: {missing_text}.",
        f"Present columns: {present_text}.",
    ]
    for target, sources in ambiguous.items():
        joined = ", ".join(sources)
        sentences.append(
            f"Multiple columns could map to required field '{target}': {joined}. "
            "Choose one in a mapping file."
        )
    sentences.extend(suggestions)
    allowed = ", ".join(REQUIRED_COLUMNS)
    if any(_contains_cjk(str(column)) for column in present):
        sentences.append(
            "Chinese headers are matched from a built-in list "
            "(bank, QuickBooks, and Shopee-style names)."
        )
    sentences.append(
        "No rows were deleted. "
        f"Rename the headers to the canonical names ({allowed}) "
        "or pass a mapping file with columns 'source' and 'target'."
    )
    return " ".join(sentences)


def map_columns(
    df: pd.DataFrame,
    mapping_path: str | Path | None = None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """
    Rename recognized columns to the canonical schema.

    Raises
    ------
    ValueError
        When a required column cannot be mapped, or several columns compete
        for the same required field. The message starts with
        ``Missing required columns``.
    """
    user_mapping = load_user_mapping(mapping_path) if mapping_path else {}
    original_columns = [str(column) for column in df.columns]
    assigned: dict[str, str] = {}
    methods: dict[str, str] = {}
    rename: dict[str, str] = {}
    skipped: list[dict[str, str]] = []
    ambiguous: dict[str, list[str]] = {}

    def claim(column: str, target: str, method: str) -> None:
        assigned[target] = column
        methods[column] = method
        if column != target:
            rename[column] = target

    unknown_user_sources = set(user_mapping)
    for column in original_columns:
        target = user_mapping.get(loose_key(column))
        if target is None:
            continue
        unknown_user_sources.discard(loose_key(column))
        if target in assigned:
            previous = assigned[target]
            raise ValueError(
                f"Mapping conflict: '{previous}' and '{column}' both map to '{target}'. "
                "Each canonical field can only come from one column."
            )
        claim(column, target, "user")

    if unknown_user_sources:
        present = ", ".join(original_columns) if original_columns else "(none)"
        unknown = ", ".join(sorted(unknown_user_sources))
        raise ValueError(
            f"Mapping file refers to unknown columns: {unknown}. Present columns: {present}."
        )

    for column in original_columns:
        if column in methods:
            continue
        if column in MAPPING_TARGETS:
            if column in assigned and assigned[column] != column:
                raise ValueError(
                    f"Mapping conflict: '{assigned[column]}' is mapped to '{column}', "
                    f"but the file also has a column already named '{column}'."
                )
            claim(column, column, "canonical")

    synonym_groups: dict[str, list[tuple[int, str]]] = {}
    for column in original_columns:
        if column in methods:
            continue
        found = SYNONYM_INDEX.get(loose_key(column))
        if found is None:
            continue
        target, priority = found
        synonym_groups.setdefault(target, []).append((priority, column))

    for target, group in synonym_groups.items():
        group.sort()
        columns = [column for _priority, column in group]
        if target in assigned:
            for column in columns:
                skipped.append(
                    {
                        "column": column,
                        "target": target,
                        "reason": f"'{assigned[target]}' already maps to '{target}'",
                    }
                )
            continue
        if target in STRICT_REQUIRED and len(columns) > 1:
            ambiguous[target] = columns
            continue
        winner = columns[0]
        claim(winner, target, "synonym")
        for column in columns[1:]:
            skipped.append(
                {
                    "column": column,
                    "target": target,
                    "reason": f"'{winner}' was selected for '{target}'",
                }
            )

    for column in original_columns:
        if column in methods or any(column in sources for sources in ambiguous.values()):
            continue
        guessed = _fuzzy_target(loose_key(column))
        if guessed is None:
            continue
        target, score, runner_up = guessed
        if score < _FUZZY_THRESHOLD or (score - runner_up) < _FUZZY_MARGIN:
            continue
        if target in assigned or target in ambiguous:
            skipped.append(
                {
                    "column": column,
                    "target": target,
                    "reason": f"fuzzy match to '{target}' ({score:.2f}) was not applied",
                }
            )
            continue
        claim(column, target, "fuzzy")

    mapped = df.rename(columns=rename)
    mapped, combined = combine_debit_credit(mapped)

    missing = [column for column in REQUIRED_COLUMNS if column not in mapped.columns]
    claimed_sources = set(methods)
    suggestions = _suggestions(original_columns, missing, claimed_sources)
    report: dict[str, Any] = {
        "applied": [
            {"source": source, "target": target, "method": methods[source]}
            for target, source in assigned.items()
        ],
        "renames": dict(rename),
        "unmapped_columns": [column for column in original_columns if column not in methods],
        "skipped": skipped,
        "ambiguous_required": ambiguous,
        "suggestions": suggestions,
        "debit_credit_combined": combined,
        "original_columns": original_columns,
    }
    if missing or ambiguous:
        raise ValueError(
            build_mapping_error(
                missing=missing,
                present=original_columns,
                ambiguous=ambiguous,
                suggestions=suggestions,
            )
        )
    return mapped, report
