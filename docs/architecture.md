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

Then verifies that expected files exist before success evidence is recorded.

## Audit evidence

`evidence/audit.jsonl` is append-only from the application’s perspective.

Success records include counts, quality score, and output file names (basename only). Notable fields:

- `quality_score` = `clean_rows / input_rows` (0.0 when `input_rows` is 0)
- `duplicates_removed` = rejected rows with reason `exact_duplicate_row` or `duplicate_transaction_id`
- `invalid_dates` / `invalid_amounts` = validation validity counts (unparseable present values), not the full reject tally
- `input_file` = file name only (never an absolute user path)

Failure records include error type/message and sanitized input file name only (no home-directory paths).

## Failure behavior

- Missing files and unsupported formats raise clear exceptions during ingestion.
- Missing required columns fail the pipeline after validation.
- Any exception during the run appends a `status=failed` evidence line, then re-raises.
- The CLI exits non-zero on failure.

## Non-goals (v1)

No database, web UI, cloud services, LLM/agents, Docker, or workflow engines.
