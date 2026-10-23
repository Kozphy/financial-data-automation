# Gumroad draft

Do not publish this listing until the license text is approved.

## Title

Kozphy Financial Automation Toolkit

## Description

A Python 3.12 toolkit that reads one CSV or Excel transaction file, checks required fields, separates duplicate and inconsistent rows, and writes a formatted Excel summary. The summary includes a notice that the numbers are calculated from the supplied file and are not an audit opinion, a forecast, or a guarantee.

The public repository currently has no LICENSE file. This draft does not claim the download is the only copy, that buyers exist, or that any result has been certified.

## Packages

| | Basic US$29 | Pro US$49 |
| --- | --- | --- |
| Source, tests, sample CSV and XLSX | Included | Included |
| User guide and formatted summary | Included | Included |
| Revenue tracking workbook template | Included | Included |
| Upwork delivery-note template | | Included |
| Email reply within 7 days about running the sample | | Included |

## Cover brief

A plain navy rectangle, 1600 by 900, with the title "Kozphy Financial Automation Toolkit" and the line "CSV and Excel transaction checks". Show four file names: cleaned workbook, rejected rows, summary, quality CSV. No people, no currency stacks, no star ratings, and no "guaranteed" wording.

## Setup

Unzip the archive, install Python 3.12, then run `py -m pip install -e ".[dev]"` and `py run_pipeline.py data\sample\sample_transactions.csv --output data\processed`.

## FAQ

**Does this connect to my bank?** No.

**Is the summary an audit?** No. The notice sheet says it is not an audit opinion.

**What data is in the sample?** Invented companies and amounts, including rows that are supposed to fail validation.

**Can I resell the source?** Not under the draft below. You may use it for your own files and client work.

## License draft

Copyright remains with the repository owner. A buyer of the Basic or Pro package may use the code and sample files to process their own data and client files. They may not republish the source archive, sell it as a toolkit, or remove the notice sentence from a report they present as this product's output. This draft is not the repository LICENSE. pandas is BSD-3-Clause, and openpyxl, pytest, and ruff are MIT; those packages are installed from PyPI and are not vendored in the ZIP. Confirm each package's current license text before publishing.

## Changelog

### Unreleased

- Formatted `financial_summary.xlsx` with a notice sheet, frozen header, and amount formats.
- CLI `--output` and `--evidence`.
- ZIP builder that omits `evidence/`.
- GitHub Actions, Dependabot, and ruff configuration.

## LinkedIn announcement draft

I published a draft Python toolkit that checks one transaction CSV or Excel file and writes a formatted summary. The notice on the workbook says the result is calculated from the supplied file and is not an audit opinion or a forecast. I am looking for one bookkeeping or finance user who wants a paid trial of that workflow at US$99. I do not have customers or reviews to show yet.
