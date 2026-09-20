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


if __name__ == "__main__":
    main()
