"""Column mapping from bank, QuickBooks, and Chinese exports."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from financial_data_automation.mapping import (
    SYNONYM_INDEX,
    _SYNONYM_GROUPS,
    loose_key,
    map_columns,
)
from financial_data_automation.validation import validate_schema


def test_synonym_table_has_one_target_per_header() -> None:
    seen: dict[str, str] = {}
    for target, synonyms in _SYNONYM_GROUPS:
        for synonym in synonyms:
            key = loose_key(synonym)
            previous = seen.get(key)
            assert previous in (None, target), f"{synonym!r} maps to both {previous} and {target}"
            seen[key] = target
    assert SYNONYM_INDEX[loose_key("訂單編號")][0] == "transaction_id"
    assert SYNONYM_INDEX[loose_key("摘要")][0] == "description"


def test_quickbooks_headers() -> None:
    frame = pd.DataFrame(
        {
            "Date": ["2026-01-01"],
            "Num": ["1001"],
            "Name": ["Acme"],
            "Memo": ["Office supplies"],
            "Amount": [120.5],
        }
    )
    mapped, report = map_columns(frame)
    assert list(mapped["transaction_id"]) == ["1001"]
    assert list(mapped["description"]) == ["Office supplies"]
    assert list(mapped["customer"]) == ["Acme"]
    assert mapped.loc[0, "amount"] == 120.5
    assert report["debit_credit_combined"] is False


def test_chinese_headers_and_keeps_unmapped() -> None:
    frame = pd.DataFrame(
        {
            "交易編號": ["A1"],
            "交易日期": ["113/05/01"],
            "摘要": ["辦公用品"],
            "金額": ["NT$10"],
            "餘額": ["NT$10"],
        }
    )
    mapped, report = map_columns(frame)
    assert set(mapped.columns) >= {"transaction_id", "date", "description", "amount", "餘額"}
    assert "餘額" in report["unmapped_columns"]


def test_description_prefers_summary_and_keeps_note() -> None:
    frame = pd.DataFrame(
        {
            "交易編號": ["A1"],
            "交易日期": ["113/05/01"],
            "摘要": ["薪資"],
            "備註": ["備註不應被刪"],
            "金額": [10],
        }
    )
    mapped, report = map_columns(frame)
    assert mapped.loc[0, "description"] == "薪資"
    assert mapped.loc[0, "備註"] == "備註不應被刪"
    assert any(item["column"] == "備註" for item in report["skipped"])


def test_fuzzy_typos() -> None:
    frame = pd.DataFrame(
        {
            "Transction ID": ["T1"],
            "Date": ["2026-01-01"],
            "Descripton": ["hello"],
            "Ammount": ["12.5"],
        }
    )
    mapped, report = map_columns(frame)
    assert list(mapped["transaction_id"]) == ["T1"]
    assert list(mapped["description"]) == ["hello"]
    assert validate_schema(mapped)["coerced_frame"].loc[0, "amount"] == 12.5
    methods = {item["target"]: item["method"] for item in report["applied"]}
    assert methods["transaction_id"] == "fuzzy"
    assert methods["amount"] == "fuzzy"


def test_balance_is_not_mapped_to_amount() -> None:
    frame = pd.DataFrame(
        {
            "transaction_id": ["T1"],
            "date": ["2026-01-01"],
            "description": ["x"],
            "balance": [99],
        }
    )
    with pytest.raises(ValueError, match="Missing required columns: amount"):
        map_columns(frame)


def test_ambiguous_amount_is_an_error() -> None:
    frame = pd.DataFrame(
        {
            "訂單編號": ["A1"],
            "交易日期": ["113/01/01"],
            "商品名稱": ["鞋子"],
            "商品總價": [100],
            "買家總支付金額": [120],
        }
    )
    with pytest.raises(ValueError, match="Multiple columns could map to required field 'amount'") as exc:
        map_columns(frame)
    assert "No rows were deleted" in str(exc.value)
    assert "商品總價" in str(exc.value)


def test_user_mapping_csv_and_json(tmp_path: Path) -> None:
    frame = pd.DataFrame(
        {
            "店內單號": ["S1"],
            "成立日": ["2026-02-01"],
            "品項說明": ["杯子"],
            "實收": ["NT$80"],
        }
    )
    csv_path = tmp_path / "map.csv"
    csv_path.write_text(
        "source,target\n店內單號,transaction_id\n成立日,date\n品項說明,description\n實收,amount\n",
        encoding="utf-8",
    )
    mapped, report = map_columns(frame, csv_path)
    assert list(mapped["transaction_id"]) == ["S1"]
    assert validate_schema(mapped)["coerced_frame"].loc[0, "amount"] == 80
    assert all(item["method"] == "user" for item in report["applied"])

    json_path = tmp_path / "map.json"
    json_path.write_text(
        json.dumps(
            {
                "店內單號": "transaction_id",
                "成立日": "date",
                "品項說明": "description",
                "實收": "金額",
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    mapped_json, _report = map_columns(frame, json_path)
    assert validate_schema(mapped_json)["coerced_frame"].loc[0, "amount"] == 80


def test_unknown_mapping_column(tmp_path: Path) -> None:
    frame = pd.DataFrame({"金額": [1]})
    path = tmp_path / "map.csv"
    path.write_text("source,target\n不存在,amount\n", encoding="utf-8")
    with pytest.raises(ValueError, match="unknown columns"):
        map_columns(frame, path)


def test_debit_credit_becomes_signed_amount_and_keeps_source_columns() -> None:
    frame = pd.DataFrame(
        {
            "交易序號": ["B1", "B2", "B3"],
            "交易日期": ["113/03/01", "113/03/02", "113/03/03"],
            "摘要": ["薪資", "超市", "壞掉的金額"],
            "支出": [None, "1,250", "abc"],
            "存入": ["NT$50,000", None, None],
            "餘額": [50000, 48750, 48750],
        }
    )
    mapped, report = map_columns(frame)
    assert report["debit_credit_combined"] is True
    assert mapped.loc[0, "amount"] == 50000
    assert mapped.loc[1, "amount"] == -1250
    assert mapped.loc[2, "amount"] == "abc"
    assert "debit" in mapped.columns
    assert "credit" in mapped.columns
    assert "餘額" in mapped.columns
