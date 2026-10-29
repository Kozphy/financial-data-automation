# Architecture

## Purpose

`financial-data-automation` is a local, deterministic pipeline that turns CSV/XLSX transaction files into cleaned datasets, financial summaries, quality reports, and append-only audit evidence.

## Input contract

Supported formats:

- `.csv`
- `.xlsx` (via openpyxl)

Legacy `.xls` is intentionally unsupported so unsupported inputs fail with a clear format error instead of a cryptic engine failure.

Required columns after normalization:

- `transaction_id`
- `date`
- `description`
- `amount`

Optional columns may include:

- `customer`, `category`, `currency`, `cost`, `quantity`, `unit_price`, `region`

Column normalization:

1. strip whitespace
2. lowercase
3. replace spaces with underscores

CSV files are read as UTF-8 (BOM allowed), UTF-16 when a BOM is present, then Big5/cp950.

## Column mapping

`mapping.py` runs after normalization and before validation.

Match order:

1. Optional user mapping file (`.csv`, `.json`, or `.xlsx`, columns `source` and `target`)
2. Header is already canonical
3. Exact synonym (English accounting/export names and Traditional Chinese, plus common Simplified forms)
4. Fuzzy match (`difflib`, threshold 0.88) for non-Chinese typos such as `ammount`

Extra columns that do not match are kept. `餘額` is intentionally not treated as `amount`.

If several columns could be the amount, the date, or the transaction id, the run stops and lists them. Description ties prefer the higher-priority synonym (for example 摘要 over 備註) and keep the other column.

When `amount` is missing but a debit/credit pair is present (`支出`/`存入`, `debit`/`credit`), the pipeline adds `amount = credit - debit`. Withdrawals become negative. The source columns stay on the row. A non-numeric debit or credit cell is copied into `amount` so validation can reject it as `invalid_amount`.

Unmapped required columns raise `ValueError` starting with `Missing required columns`, including the headers that were present. No rows are deleted on that failure.

## Dates and amounts

`formats.py` parses:

- ROC dates: `113/05/01`, `113年5月1日`, `民國113年5月1日`, full-width digits. A 3-digit year is 民國 (year + 1911). `2026-01-01` and `2024年5月1日` stay Gregorian.
- Amounts: `NT$1,234.50`, thousands separators, full-width digits, and parentheses for negatives.

Plain numbers and ISO dates keep the previous behavior. `abc` and `not-a-date` are still invalid.

## Validation boundary

`validation.py` is responsible for:

- detecting missing required columns
- coercing `date` → datetime and `amount` → numeric where possible
- counting **invalid dates/amounts** as present, non-blank values that fail to parse
- counting **duplicate transaction IDs** as the number of rows whose `transaction_id` value is not unique (includes the first occurrence)
- counting **null/blank required fields** on pre-coercion values (so completeness is not inflated by parse failures that become NaT/NaN)
- checking non-negative optional numeric fields when present
- checking `quantity * unit_price` consistency against `amount` when both sides exist

Validation **reports** issues. It does not permanently delete rows.

After coercion, cleaning may quarantine null dates/amounts under `invalid_date` / `invalid_amount` reject reasons. Audit `invalid_dates` / `invalid_amounts` remain the validation validity counts above; `rejected_rows` is the full quarantine count.

## Cleaning boundary

`cleaning.py` is responsible for:

- removing exact duplicate rows into the reject set
- quarantining rows with missing/invalid required values
- quarantining duplicate `transaction_id` rows (keeping the first)
- quarantining negative optional measures when present
- attaching a `reject_reason` to every rejected row

Validation and cleaning are separate so that:

- quality measurement remains explicit
- business filtering rules stay reviewable
- rejected records remain available as evidence

## Rejected-record handling

Rejected rows are written to `rejected_rows.xlsx` and counted in audit evidence. Reasons include:

- `exact_duplicate_row`
- `missing_transaction_id`
- `invalid_date`
- `invalid_amount`
- `missing_description`
- `duplicate_transaction_id`
- `negative_quantity` / `negative_unit_price` / `negative_cost`

## Analytics

`analytics.py` computes:

- record count
- total / average / min / max amount
- gross profit and gross margin when `cost` exists
- monthly totals by calendar month

Gross profit/margin use only rows where both `amount` and `cost` are present (missing cost is not treated as zero). Gross margin uses that subset’s total amount as the denominator and returns `None` when the denominator is zero.

Quality score:

```text
clean_rows / input_rows
```

## Reporting

`reporting.py` writes:

- `cleaned_data.xlsx`
- `rejected_rows.xlsx`
- `financial_summary.xlsx` (`summary`, `monthly`, `quality` sheets)
- `quality_report.csv`

Pass `language="zh-TW"` to use Traditional Chinese column headers, sheet names (`摘要`, `每月合計`, `品質`), a `剔除說明` column on rejected rows, and a `說明` column on the quality report. English output keeps the canonical header names. Quality checks `columns_mapped` and `debit_credit_combined` are included in the quality report.

`streamlit_app.py` is a local upload page over the same `run_pipeline` function. It is not a separate cleaning implementation.

`verify_outputs` checks that the expected files exist before success evidence is recorded.

## Audit evidence

`evidence/audit.jsonl` is append-only from the application’s perspective.

Success records include counts, quality score, and output file names (basename only). Notable fields:

- `quality_score` = `clean_rows / input_rows` (0.0 when `input_rows` is 0)
- `duplicates_removed` = rejected rows with reason `exact_duplicate_row` or `duplicate_transaction_id`
- `invalid_dates` / `invalid_amounts` = validation validity counts (unparseable present values), not the full reject tally
- `input_file` = file name only (never an absolute user path)
- `language`, `columns_mapped`, and `debit_credit_combined` record the mapping run
- `mapping_file` is the mapping file name only, and only when one was supplied

Failure records include error type/message and sanitized input file name only (no home-directory paths).

## Failure behavior

- Missing files and unsupported formats raise clear exceptions during ingestion.
- Missing required columns fail the pipeline during column mapping (or validation if a required field is still absent). The error names the missing fields and the headers that were present.
- Any exception during the run appends a `status=failed` evidence line, then re-raises.
- The CLI exits non-zero on failure.

## Non-goals

No database, hosted service, cloud storage, LLM/agents, Docker, or workflow engine. The web UI is a local Streamlit page, not a multi-user server.
