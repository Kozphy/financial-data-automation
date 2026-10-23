# Upwork copy

Do not send any of this until a specific prospect is approved.

## Title

Excel and CSV financial report automation for transaction files

## Profile overview

I build Python workflows that turn one transaction export into a checked Excel workbook. The work covers CSV and XLSX imports, missing values, invalid dates and amounts, duplicate rows, and a summary a finance user can open. Rejected rows stay visible with a reason. I work in Python, pandas, pytest, and GitHub Actions. I am based in Taiwan and deliver remotely in English. I do not provide an audit opinion, a forecast, or a claim that a report will change a financial result.

## Packages

### Starter — US$99

One transaction file, up to 5,000 rows and 20 columns. Deliver a cleaned workbook, a rejection workbook, a formatted summary, and a short note of what was removed. One revision of column mapping.

### Standard — US$199

Everything in Starter, plus a second source file, a monthly sheet, and a quality count. Two revisions of column mapping. Still one reporting period.

### Advanced — US$399

Everything in Standard, plus a repeatable command the client can run locally, a sample file, and a written runbook. Three revisions. No hosting, no login, and no scheduled job.

## Out of scope for all packages

Audit opinions, tax advice, forecasts, bank connections, bookkeeping entries into a ledger, more than the stated files, and any file that contains credentials. Real customer data is processed only after the client sends it for a paid engagement. This repository's samples are synthetic.

## Discovery questions

1. Which file format do you export today, CSV or Excel?
2. Which columns must appear in the summary?
3. How many rows are in a normal month?
4. What should happen to duplicates and blank descriptions?
5. Who opens the workbook, and which totals do they check by hand?
6. Is cost present on every row, or only some rows?
7. Do you need this once, or every month on your own computer?
8. Which columns must never leave your machine?

## Onboarding checklist

- Confirm the package and the file count in writing.
- Receive a sample or a redacted file. Refuse live credentials.
- Map source headers to `transaction_id`, `date`, `description`, and `amount`.
- Run the pipeline locally and return the four outputs.
- Walk through rejected rows before calling the job done.

## Acceptance

- The command exits 0 on the agreed file.
- Required columns are present or the run fails with the missing names.
- Rejected rows are listed and are not silently dropped.
- The notice sheet contains the non-audit, non-forecast sentence.
- Amount columns use `#,##0.00`.
- The delivery note states input, clean, and rejected counts.

## Proposal templates

1. **Messy export.** I can turn your transaction CSV into a cleaned workbook, a rejection list, and a one-page summary. The summary states it is calculated from your file and is not an audit opinion. Starter is US$99 for one file up to 5,000 rows.
2. **Duplicate rows.** I can separate exact duplicate rows and repeated transaction ids, keep the first clean row, and show the removed rows with a reason. The same Starter limit applies.
3. **Excel month-end.** I can read your XLSX export, check dates and amounts, and return monthly totals plus a quality count. Standard is US$199 when a second file or a monthly sheet is required.
4. **Repeatable local run.** I can leave you a command and a runbook so the next export does not need another project. Advanced is US$399. I do not host the file.
5. **Column mapping.** If your headers differ from transaction id, date, description, and amount, I will map them once and document the mapping. That mapping is included in the revision count for the selected package.

## Delivery report

```text
Client:
Package:
Input file name:
Input rows:
Clean rows:
Rejected rows:
Outputs: cleaned_data.xlsx, rejected_rows.xlsx, financial_summary.xlsx, quality_report.csv
Notice reviewed: yes
Open items:
```
