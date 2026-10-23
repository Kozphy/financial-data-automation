# User guide

This toolkit reads one CSV or Excel transaction file and writes four outputs:

- `cleaned_data.xlsx` — rows kept after validation.
- `rejected_rows.xlsx` — rows removed, with the reason kept visible.
- `financial_summary.xlsx` — totals, monthly totals, quality counts, and a notice that the result is not an audit opinion or a forecast.
- `quality_report.csv` — the same quality counts in CSV form.

## Setup

Python 3.12 or newer is required.

```powershell
py -m pip install -e ".[dev]"
```

## Run

```powershell
py run_pipeline.py data\sample\sample_transactions.csv --output data\processed
```

The sample file is synthetic. It contains an exact duplicate, a repeated transaction id, a blank description, an invalid date, and an invalid amount so the rejection workbook is not empty.

## Required columns

`transaction_id`, `date`, `description`, and `amount`. Extra columns such as `cost`, `quantity`, and `unit_price` are used when present. A missing cost is not treated as zero.

## What a buyer receives

The command prints input, clean, and rejected counts. Open `financial_summary.xlsx` and read the `notice` sheet before using any total.
