"""Generate synthetic sample transaction files for the demo."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def build_sample_frame() -> pd.DataFrame:
    """Create a small synthetic dataset with intentional quality issues."""
    rows = [
        {
            "Transaction ID": "TXN-001",
            "Date": "2026-01-05",
            "Description": "Office supplies",
            "Amount": 120.50,
            "Customer": "Acme Co",
            "Category": "ops",
            "Currency": "USD",
            "Cost": 40.00,
            "Quantity": 5,
            "Unit Price": 24.10,
            "Region": "west",
        },
        {
            "Transaction ID": "TXN-002",
            "Date": "2026-01-08",
            "Description": "Consulting hours",
            "Amount": 1500.00,
            "Customer": "Beta LLC",
            "Category": "services",
            "Currency": "USD",
            "Cost": 600.00,
            "Quantity": 10,
            "Unit Price": 150.00,
            "Region": "east",
        },
        {
            "Transaction ID": "TXN-003",
            "Date": "2026-02-01",
            "Description": "Software subscription",
            "Amount": 299.99,
            "Customer": "Acme Co",
            "Category": "saas",
            "Currency": "USD",
            "Cost": 50.00,
            "Quantity": 1,
            "Unit Price": 299.99,
            "Region": "west",
        },
        # Exact duplicate of TXN-001 row
        {
            "Transaction ID": "TXN-001",
            "Date": "2026-01-05",
            "Description": "Office supplies",
            "Amount": 120.50,
            "Customer": "Acme Co",
            "Category": "ops",
            "Currency": "USD",
            "Cost": 40.00,
            "Quantity": 5,
            "Unit Price": 24.10,
            "Region": "west",
        },
        # Duplicate transaction_id with different payload
        {
            "Transaction ID": "TXN-002",
            "Date": "2026-01-09",
            "Description": "Consulting hours adjustment",
            "Amount": 100.00,
            "Customer": "Beta LLC",
            "Category": "services",
            "Currency": "USD",
            "Cost": 20.00,
            "Quantity": 1,
            "Unit Price": 100.00,
            "Region": "east",
        },
        # Missing description
        {
            "Transaction ID": "TXN-004",
            "Date": "2026-02-10",
            "Description": None,
            "Amount": 75.00,
            "Customer": "Gamma Inc",
            "Category": "ops",
            "Currency": "USD",
            "Cost": 10.00,
            "Quantity": 3,
            "Unit Price": 25.00,
            "Region": "central",
        },
        # Invalid date
        {
            "Transaction ID": "TXN-005",
            "Date": "not-a-date",
            "Description": "Travel reimbursement",
            "Amount": 220.00,
            "Customer": "Delta SA",
            "Category": "travel",
            "Currency": "USD",
            "Cost": 220.00,
            "Quantity": 1,
            "Unit Price": 220.00,
            "Region": "east",
        },
        # Invalid amount
        {
            "Transaction ID": "TXN-006",
            "Date": "2026-02-15",
            "Description": "Misc fee",
            "Amount": "abc",
            "Customer": "Echo GmbH",
            "Category": "fees",
            "Currency": "USD",
            "Cost": 0.00,
            "Quantity": 1,
            "Unit Price": 0.00,
            "Region": "west",
        },
        # Valid March row
        {
            "Transaction ID": "TXN-007",
            "Date": "2026-03-03",
            "Description": "Hardware purchase",
            "Amount": 899.00,
            "Customer": "Acme Co",
            "Category": "capex",
            "Currency": "USD",
            "Cost": 700.00,
            "Quantity": 1,
            "Unit Price": 899.00,
            "Region": "west",
        },
    ]
    return pd.DataFrame(rows)


def build_taiwan_frame() -> pd.DataFrame:
    """Traditional Chinese headers, ROC dates, and TWD amounts, with bad rows."""
    rows = [
        {
            "交易編號": "TXN-101",
            "交易日期": "113/05/01",
            "摘要": "辦公用品",
            "金額": "NT$1,200.50",
            "客戶": "台北商行",
            "類別": "營運",
            "幣別": "TWD",
            "成本": "NT$400.00",
            "數量": 5,
            "單價": "NT$240.10",
            "地區": "北區",
        },
        {
            "交易編號": "TXN-102",
            "交易日期": "113年5月8日",
            "摘要": "顧問服務",
            "金額": "2,500",
            "客戶": "高雄企業",
            "類別": "服務",
            "幣別": "TWD",
            "成本": 800,
            "數量": 1,
            "單價": 2500,
            "地區": "南區",
        },
        {
            "交易編號": "TXN-103",
            "交易日期": "113/06/01",
            "摘要": "退貨",
            "金額": "(NT$300.00)",
            "客戶": "台北商行",
            "類別": "營運",
            "幣別": "TWD",
            "成本": 0,
            "數量": 1,
            "單價": 0,
            "地區": "北區",
        },
        # Exact duplicate of TXN-101
        {
            "交易編號": "TXN-101",
            "交易日期": "113/05/01",
            "摘要": "辦公用品",
            "金額": "NT$1,200.50",
            "客戶": "台北商行",
            "類別": "營運",
            "幣別": "TWD",
            "成本": "NT$400.00",
            "數量": 5,
            "單價": "NT$240.10",
            "地區": "北區",
        },
        {
            "交易編號": "TXN-104",
            "交易日期": "113/06/15",
            "摘要": None,
            "金額": "500",
            "客戶": "台中店",
            "類別": "營運",
            "幣別": "TWD",
            "成本": 100,
            "數量": 1,
            "單價": 500,
            "地區": "中區",
        },
        {
            "交易編號": "TXN-105",
            "交易日期": "不是日期",
            "摘要": "交通費",
            "金額": "220",
            "客戶": "台中店",
            "類別": "差旅",
            "幣別": "TWD",
            "成本": 220,
            "數量": 1,
            "單價": 220,
            "地區": "中區",
        },
        {
            "交易編號": "TXN-106",
            "交易日期": "113/07/01",
            "摘要": "雜費",
            "金額": "abc",
            "客戶": "新竹店",
            "類別": "費用",
            "幣別": "TWD",
            "成本": 0,
            "數量": 1,
            "單價": 0,
            "地區": "北區",
        },
        {
            "交易編號": "TXN-107",
            "交易日期": "１１３／０８／０１",
            "摘要": "設備",
            "金額": "１，５００",
            "客戶": "新竹店",
            "類別": "資本",
            "幣別": "TWD",
            "成本": 900,
            "數量": 1,
            "單價": 1500,
            "地區": "北區",
        },
    ]
    return pd.DataFrame(rows)


def build_bank_frame() -> pd.DataFrame:
    """Taiwan bank-statement shape: 支出 / 存入 instead of a single amount column."""
    return pd.DataFrame(
        [
            {
                "交易序號": "B001",
                "交易日期": "113/03/01",
                "摘要": "薪資轉入",
                "支出": None,
                "存入": "NT$50,000",
                "餘額": "NT$50,000",
            },
            {
                "交易序號": "B002",
                "交易日期": "113年3月2日",
                "摘要": "超市",
                "支出": "1,250",
                "存入": None,
                "餘額": "NT$48,750",
            },
        ]
    )


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    sample_dir = root / "data" / "sample"
    sample_dir.mkdir(parents=True, exist_ok=True)
    df = build_sample_frame()
    xlsx = sample_dir / "sample_transactions.xlsx"
    csv = sample_dir / "sample_transactions.csv"
    df.to_excel(xlsx, index=False)
    df.to_csv(csv, index=False)
    print(f"Wrote {xlsx.relative_to(root).as_posix()}")
    print(f"Wrote {csv.relative_to(root).as_posix()}")

    taiwan = build_taiwan_frame()
    taiwan_csv = sample_dir / "sample_transactions_zh_tw.csv"
    taiwan_xlsx = sample_dir / "sample_transactions_zh_tw.xlsx"
    taiwan.to_csv(taiwan_csv, index=False, encoding="utf-8-sig")
    taiwan.to_excel(taiwan_xlsx, index=False)
    print(f"Wrote {taiwan_csv.relative_to(root).as_posix()}")
    print(f"Wrote {taiwan_xlsx.relative_to(root).as_posix()}")

    bank = build_bank_frame()
    bank_csv = sample_dir / "sample_bank_statement_zh_tw.csv"
    bank.to_csv(bank_csv, index=False, encoding="utf-8-sig")
    print(f"Wrote {bank_csv.relative_to(root).as_posix()}")


if __name__ == "__main__":
    main()
