# Capability audit

Repository: https://github.com/Kozphy/financial-data-automation
Commit audited: `0887267` on `master`, then the formatted-report branch.
Public license API: HTTP 404. No `LICENSE` file was present.

| Capability | Status | Evidence |
| --- | --- | --- |
| CSV and XLSX import, normalized headers | Verified and reusable | `src/financial_data_automation/ingestion.py`, `tests/test_ingestion.py` |
| Required columns, blanks, invalid dates and amounts | Verified and reusable | `validation.py`, `tests/test_validation.py` |
| Duplicate ids, exact duplicate rows, quantity times price | Verified and reusable | `cleaning.py`, `validation.py`, `tests/test_pipeline.py` |
| Summary and monthly totals; missing cost is not zero | Verified and reusable | `analytics.py`, `tests/test_analytics.py` |
| Plain Excel and CSV outputs | Partially implemented before this branch | `reporting.py` used `DataFrame.to_excel` with no notice, freeze, or number format |
| Formatted client workbook | Implemented on this branch | `tests/test_reporting.py` |
| Synthetic sample | Verified and reusable | `data/sample/sample_transactions.csv` |
| CLI | Partially implemented before this branch; `--output` added here | `run_pipeline.py`, `tests/test_cli.py` |
| User guide | Partially implemented; `docs/USER_GUIDE.md` added here | `README.md`, `docs/architecture.md` |
| pytest | Verified and reusable | `tests/` |
| ruff | Missing before this branch | `pyproject.toml` had no ruff extra |
| GitHub Actions CI | Missing before this branch | only the dynamic Dependabot graph workflow existed |
| Dependabot config | Missing before this branch | no `.github/dependabot.yml` |
| Distributable ZIP | Missing before this branch | `packaging.py`, `tests/test_package.py` |
| Repository license | Missing | GitHub license endpoint returned 404 |
| Hosted SaaS, billing, scheduling | Missing | no upload, account, or scheduler code |

Other public repositories were not selected. `financial-fraud-risk-engine` also has no detectable license. `EvalForge` is marked other/proprietary. `crypto-performance-analyzer` does not contain this transaction pipeline. `freqtrade` and `bbgo` are third-party codebases.

## Smallest paid problem

One customer supplies one CSV or XLSX of transactions. The deliverable is a cleaned workbook, a rejection workbook, and a formatted summary that states it is not an audit opinion and not a forecast. That is the US$99 Starter. No schedule and no forecast are included.
