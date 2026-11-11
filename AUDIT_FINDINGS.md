# Audit Findings — Financial Data Automation

**Repository:** https://github.com/Kozphy/financial-data-automation  
**Audit mode:** READ-ONLY (no application source changes, no commit/push/deploy)  
**Audit date:** 2026-11-09  
**Scope:** `src/financial_data_automation/*`, `tests/*`, `run_pipeline.py`, `scripts/*`, `docs/*`, `data/sample/*`, dependency manifests  
**Method:** Claim → Evidence → Verification → Decision  

## Execution evidence (tests)

| Activity | Result | Notes |
|---|---|---|
| `python -m pytest -v --tb=short` | **15 passed** in 2.27s | Executed in local `.venv` (Python 3.12.10) |
| Adversarial probe script (synthetic data only, temp dirs) | Executed | Float, qty×price, Excel injection, FX sum, partition, mapping, hashing absence |
| Dependency CVE scan (`pip-audit`) | **NOT VERIFIED** | `pip_audit` not installed; not invented |

Installed packages observed: `pandas==3.0.6` (BSD-3-Clause), `openpyxl==3.1.5` (MIT), `pytest==9.1.1` (MIT).

---

## Verification status legend

| Status | Meaning |
|---|---|
| **CONFIRMED** | Static code inspection proves the condition |
| **REPRODUCED** | Dynamic probe/test executed and observed the condition |
| **CODE-INDICATED** | Code/docs strongly indicate the condition; dynamic proof optional or N/A |
| **NOT FOUND** | Searched; control or vulnerability not present |
| **NOT VERIFIED** | Could not safely/feasibly verify in this audit |

---

## P0 — Financial correctness

### F-FIN-01 — Monetary amounts use IEEE-754 floats without Decimal policy

| Field | Value |
|---|---|
| **Finding ID** | F-FIN-01 |
| **Severity** | P0 |
| **Affected module** | `src/financial_data_automation/analytics.py`, `validation.py`, `cleaning.py`, `reporting.py` |
| **Evidence** | Amounts coerced via `pd.to_numeric` (`validation.py` L61–66). Totals via `float(amounts.sum())` (`analytics.py` L27–31). No `Decimal` usage anywhere under `src/` (grep). |
| **Business impact** | Ledger-style totals can differ from bank/GL expectation by ulps; undermines financial attestation. |
| **Reproduction steps** | See ADV-FLOAT-01: `compute_financial_summary` on amounts `[0.1, 0.2, 0.3]` → `total_amount=0.6000000000000001` (`== 0.6` is `False`). |
| **Recommended fix** | Store/compute money as `Decimal` (or integer minor units); define banker's vs half-up rounding; serialize with fixed scale (e.g. 2). |
| **Regression test** | Assert `0.1+0.2+0.3` monetary sum equals exact `Decimal('0.6')` after policy; property tests on random cent amounts. |
| **Verification status** | **REPRODUCED** |

### F-FIN-02 — No input↔output amount reconciliation bridge

| Field | Value |
|---|---|
| **Finding ID** | F-FIN-02 |
| **Severity** | P0 |
| **Affected module** | `pipeline.py`, `evidence.py`, `analytics.py` |
| **Evidence** | Success evidence keys (`evidence.py` L50–63) include row counts but **no** `input_amount_total`, `clean_amount_total`, `rejected_amount_total`, or variance. Pipeline never asserts amount conservation. |
| **Business impact** | Auditor cannot prove rejected amounts explain the gap between source and reported totals; silent omission risk for material lines. |
| **Reproduction steps** | ADV-OMIT-01: input amounts 100 + 50; invalid date quarantines 50; summary `total_amount=100.0` with no bridge field. ADV-REC-01: evidence keys listed without amount totals. |
| **Recommended fix** | Emit and assert `input_total = clean_total + rejected_total` (with Decimal); fail or warn on variance beyond epsilon policy. |
| **Regression test** | Pipeline test: material rejected amount must appear in evidence and reconcile. |
| **Verification status** | **REPRODUCED** + **CODE-INDICATED** |

### F-FIN-03 — `quantity * unit_price` mismatches are reported but not quarantined

| Field | Value |
|---|---|
| **Finding ID** | F-FIN-03 |
| **Severity** | P0 |
| **Affected module** | `validation.py` L82–94; `cleaning.py` (no corresponding reject); `pipeline.py` L91–95 |
| **Evidence** | Validation counts `inconsistent_quantity_price` with tolerance `1e-6`. Cleaning has no reject reason for this case. Quality report surfaces the count only. |
| **Business impact** | Financially inconsistent rows enter `cleaned_data.xlsx` and drive summary/monthly totals. |
| **Reproduction steps** | ADV-QTY-01: qty=2, unit_price=40, amount=100 → `inconsistent=1`, `clean=1`, `rejected=0`. |
| **Recommended fix** | Quarantine (or configurable severity) with `reject_reason=inconsistent_quantity_price`; optionally auto-correct only under explicit policy. |
| **Regression test** | Assert mismatched row lands in `rejected_rows` and is absent from cleaned totals. |
| **Verification status** | **REPRODUCED** |

### F-FIN-04 — Duplicate `transaction_id` keep-first can retain the wrong financial amount

| Field | Value |
|---|---|
| **Finding ID** | F-FIN-04 |
| **Severity** | P0 |
| **Affected module** | `cleaning.py` L84–90 |
| **Evidence** | `duplicated(keep="first")` keeps file order first occurrence; no “latest by date”, hash compare, or analyst choice. |
| **Business impact** | Correction/adjustment rows arriving later are discarded; retained amount may be materially wrong. |
| **Reproduction steps** | ADV-DUP-01: amounts 10 then 999 for same id → cleaned keeps `10.0`. Sample file: TXN-002 adjustment `$100` rejected; original `$1500` kept. |
| **Recommended fix** | Documented retention policy (latest timestamp, max version, manual review queue); record both payloads in rejects with linkage. |
| **Regression test** | Fixture where later duplicate is the economically correct amount; assert policy outcome. |
| **Verification status** | **REPRODUCED** |

### F-FIN-05 — Multi-currency amounts summed without FX or currency guard

| Field | Value |
|---|---|
| **Finding ID** | F-FIN-05 |
| **Severity** | P0 |
| **Affected module** | `analytics.py` `compute_financial_summary` / `compute_monthly_totals` |
| **Evidence** | Sample schema includes `Currency` (`data/sample/sample_transactions.csv`); analytics ignore currency and sum `amount` directly. |
| **Business impact** | USD+EUR (etc.) reported as a single total → false revenue/expense figures. |
| **Reproduction steps** | ADV-FX-01: USD 100 + EUR 100 → `total_amount=200.0`. |
| **Recommended fix** | Require single currency or group by currency; block cross-currency aggregate without FX table. |
| **Regression test** | Mixed currency input must fail closed or emit per-currency totals only. |
| **Verification status** | **REPRODUCED** |

### F-FIN-06 — Negative amounts accepted with no revenue/expense or sign policy

| Field | Value |
|---|---|
| **Finding ID** | F-FIN-06 |
| **Severity** | P0 |
| **Affected module** | `cleaning.py`, `analytics.py` |
| **Evidence** | Negative optional fields (`quantity`/`unit_price`/`cost`) quarantined (`cleaning.py` L92–99); **negative `amount` is not**. Probe: amount `-25.0` remains cleaned; summary total `-25.0`. |
| **Business impact** | Refunds/chargebacks/expenses may be mis-modeled; no classification into revenue vs expense. |
| **Reproduction steps** | NEG-AMT probe: `clean=1 rejected=0 total=-25.0`. |
| **Recommended fix** | Explicit signed-amount policy + optional `transaction_type` / revenue-expense mapping. |
| **Regression test** | Policy matrix for negative/positive amounts and expected classification. |
| **Verification status** | **REPRODUCED** |

### F-FIN-07 — Control present: cleaned+rejected row partition (no silent row drop)

| Field | Value |
|---|---|
| **Finding ID** | F-FIN-07 |
| **Severity** | Informational (positive control) |
| **Affected module** | `cleaning.py`; asserted in `tests/test_cleaning.py` L23–24 |
| **Evidence** | ADV-PART-01 and sample run: `len(clean)+len(rejected)==len(input)`. Sample: 9 → 4 clean + 5 rejected. |
| **Business impact** | Mitigates silent **row** loss; does **not** mitigate amount/FX/float issues above. |
| **Reproduction steps** | Run cleaning on adversarial/sample frames; assert partition equality. |
| **Recommended fix** | Keep; extend partition concept to amount reconciliation (F-FIN-02). |
| **Regression test** | Already partially covered; extend to amount totals. |
| **Verification status** | **REPRODUCED** (control works) |

---

## P0 — Privacy and security

### F-SEC-01 — Excel formula injection via unsanitized cell values

| Field | Value |
|---|---|
| **Finding ID** | F-SEC-01 |
| **Severity** | P0 |
| **Affected module** | `reporting.py` L32–33 (`DataFrame.to_excel`) |
| **Evidence** | No sanitization of leading `= + - @` in string fields. ADV-XLSX-01 wrote `description="=cmd|'/c calc'!A0"` and `customer='+1234+5678'`; openpyxl read-back retained formula-like strings. |
| **Business impact** | Analyst opening `cleaned_data.xlsx` / `rejected_rows.xlsx` may execute formulas; risk when untrusted vendor files are re-exported. |
| **Reproduction steps** | Write cleaned frame with formula-like description through `write_reports`; open with Excel or inspect via openpyxl. |
| **Recommended fix** | Prefix apostrophe / use openpyxl cell types as text; strip/neutralize formula prefixes on all string columns before export (also CSV). |
| **Regression test** | Export payload starting with `=`; assert cell is text and does not evaluate. |
| **Verification status** | **REPRODUCED** |

### F-SEC-02 — Hardcoded credentials / secrets

| Field | Value |
|---|---|
| **Finding ID** | F-SEC-02 |
| **Severity** | P0 (search objective) |
| **Affected module** | Repository-wide |
| **Evidence** | Ripgrep for password/secret/api_key/token/Bearer/aws_/private_key/BEGIN: **no matches**. `.env` ignored in `.gitignore`. |
| **Business impact** | N/A — no secret material found in tree. |
| **Reproduction steps** | Repo-wide pattern search. |
| **Recommended fix** | Maintain secret scanning in CI. |
| **Regression test** | CI secret scan job. |
| **Verification status** | **NOT FOUND** (no secrets) |

### F-SEC-03 — Unintended external network calls / uploads

| Field | Value |
|---|---|
| **Finding ID** | F-SEC-03 |
| **Severity** | P0 (search objective) |
| **Affected module** | `src/**/*.py` |
| **Evidence** | AST import set: `__future__`, `datetime`, `json`, `pandas`, `pathlib`, `typing`, `uuid`, package internals — **no** `requests`, `urllib`, `http`, `socket`, `subprocess`. Docs state local-only non-goals. |
| **Business impact** | N/A — no outbound client code found. |
| **Reproduction steps** | Static import inventory. |
| **Recommended fix** | Keep dependency surface minimal; block network in CI sandboxes if promoted. |
| **Regression test** | Import allowlist test. |
| **Verification status** | **NOT FOUND** (no network client) |

### F-SEC-04 — PII / financial row content in logs and evidence

| Field | Value |
|---|---|
| **Finding ID** | F-SEC-04 |
| **Severity** | P1 (residual risk) / objective P0 reviewed |
| **Affected module** | `evidence.py`, `run_pipeline.py`, `reporting.py` |
| **Evidence** | Evidence stores counts + basenames, not row payloads (`evidence.py` L50–63). CLI prints aggregates only (`run_pipeline.py` L31–46). **However**, outputs (`cleaned_data.xlsx`) contain customer/description fields from input by design. Sample data is synthetic (README). Failure `error_message` is `str(exception)` — path sanitization exists for input name; OS errors could still embed paths depending on exception source. |
| **Business impact** | JSONL evidence is relatively safe; Excel outputs are the PII/financial exposure surface if real data is used. |
| **Reproduction steps** | Inspect evidence record keys; inspect cleaned workbook columns. |
| **Recommended fix** | Document data classification; optional field redaction profiles; ensure exceptions never embed absolute paths. |
| **Regression test** | Evidence must not contain customer names from fixture. |
| **Verification status** | **CODE-INDICATED** (outputs hold business fields); evidence row-PII **NOT FOUND** |

### F-SEC-05 — File path / output directory safety

| Field | Value |
|---|---|
| **Finding ID** | F-SEC-05 |
| **Severity** | P1 (local trusted-operator tool) / elevate if multi-tenant |
| **Affected module** | `ingestion.py`, `pipeline.py`, `reporting.py` |
| **Evidence** | `load_data` opens arbitrary existing path; `output_dir.mkdir(parents=True)` writes wherever caller specifies (PATH-WRITE probe True). `FileNotFoundError` message uses `file_path.name` only (`ingestion.py` L36). Pipeline return `outputs` are absolute paths (ADV-PATH-01); evidence stores basenames. |
| **Business impact** | For a local CLI this is expected; unsafe if wrapped as a service accepting untrusted paths. Absolute paths in process results may leak workspace layout. |
| **Reproduction steps** | ADV-PATH-01; PATH-WRITE probe. |
| **Recommended fix** | Optional allowlist root; return relative paths; refuse writes outside workspace when `FDA_STRICT_PATHS=1`. |
| **Regression test** | Attempt write outside allowlist → error. |
| **Verification status** | **REPRODUCED** |

### F-SEC-06 — Dependency vulnerability inventory

| Field | Value |
|---|---|
| **Finding ID** | F-SEC-06 |
| **Severity** | P0 objective / status incomplete |
| **Affected module** | `requirements.txt`, `pyproject.toml` |
| **Evidence** | `pip_audit` module absent (`False`). Unpinned lower bounds only (`pandas>=2.2`, `openpyxl>=3.1`). Installed `pandas==3.0.6` while latest index showed `3.1.1`. |
| **Business impact** | Unknown CVE exposure; unreproducible builds. |
| **Reproduction steps** | `python -c "import importlib.util; print(importlib.util.find_spec('pip_audit'))"` → `None`. |
| **Recommended fix** | Add lockfile; run `pip-audit` / OSV in CI; pin versions. |
| **Regression test** | CI fails on known high/critical CVEs. |
| **Verification status** | **NOT VERIFIED** (scanner not run) |

---

## P1 — Excel and validation

### F-VAL-01 — No Excel/CSV formula-injection defenses or tests

| Field | Value |
|---|---|
| **Finding ID** | F-VAL-01 |
| **Severity** | P1 (linked to F-SEC-01) |
| **Affected module** | `reporting.py`, `tests/*` |
| **Evidence** | No tests reference formula prefixes; export uses raw `to_excel`/`to_csv`. |
| **Business impact** | Regression of F-SEC-01 likely if untested. |
| **Reproduction steps** | Grep tests for `=` / formula — absent; ADV-XLSX-01 reproduces issue. |
| **Recommended fix** | Shared sanitize helper + tests for xlsx and csv. |
| **Regression test** | Dedicated `test_excel_formula_injection_neutralized`. |
| **Verification status** | **CONFIRMED** (gap) / exploit **REPRODUCED** |

### F-VAL-02 — Incorrect column mapping fails closed (control)

| Field | Value |
|---|---|
| **Finding ID** | F-VAL-02 |
| **Severity** | Informational (positive) |
| **Affected module** | `ingestion.py`, `validation.py`, `pipeline.py` |
| **Evidence** | ADV-MAP-01: headers `txn_id,dt,desc,amt` → missing required columns; pipeline raises (`test_pipeline_failure_writes_evidence`). |
| **Business impact** | Prevents wrong-column silent processing for renamed headers. |
| **Reproduction steps** | ADV-MAP-01. |
| **Recommended fix** | Optional alias map documented for common synonyms. |
| **Regression test** | Already covered for missing columns. |
| **Verification status** | **REPRODUCED** |

### F-VAL-03 — Malformed amounts with currency symbols rejected (strict parse)

| Field | Value |
|---|---|
| **Finding ID** | F-VAL-03 |
| **Severity** | P1 (data usability / DQ) |
| **Affected module** | `validation.py` |
| **Evidence** | ADV-AMT-01: `"$12.50"` → `invalid_amounts=1`, quarantined. No locale/`$` stripping. |
| **Business impact** | Real-world exports may over-quarantine; or correctly fail closed depending on policy. Needs explicit product decision. |
| **Reproduction steps** | ADV-AMT-01. |
| **Recommended fix** | Document accepted amount grammars; optional currency-symbol strip under audit flag. |
| **Regression test** | Table of accepted/rejected amount strings. |
| **Verification status** | **REPRODUCED** |

### F-VAL-04 — No revenue/expense classification logic

| Field | Value |
|---|---|
| **Finding ID** | F-VAL-04 |
| **Severity** | P1 |
| **Affected module** | `analytics.py` |
| **Evidence** | Summary keys: record_count, total/avg/min/max amount, optional gross_profit/margin — no type/sign/category rollup. ADV-CLS-01. |
| **Business impact** | Cannot support P&L-style controls from this pipeline alone. |
| **Reproduction steps** | Inspect `compute_financial_summary` return keys. |
| **Recommended fix** | Add explicit classification rules or declare out-of-scope in README/architecture. |
| **Regression test** | Classification fixture once implemented. |
| **Verification status** | **CODE-INDICATED** / capability **NOT FOUND** |

### F-VAL-05 — Validation vs cleaning metric mismatch for blank amounts

| Field | Value |
|---|---|
| **Finding ID** | F-VAL-05 |
| **Severity** | P1 |
| **Affected module** | `validation.py`, `cleaning.py`, evidence fields |
| **Evidence** | Blank amount `"  "`: `invalid_amounts=0` but `null_required_fields.amount=1`; cleaning reject_reason=`invalid_amount` (BLANK-AMT probe). Architecture doc notes validity vs completeness split, but reject reason label still says `invalid_amount`. |
| **Business impact** | Audit metrics can understate “invalid amounts” while rejects say invalid — reconciliation confusion. |
| **Reproduction steps** | BLANK-AMT probe. |
| **Recommended fix** | Align reject reasons with validation categories (`missing_amount` vs `invalid_amount`); evidence should expose both. |
| **Regression test** | Blank vs non-parseable amount separate asserts. |
| **Verification status** | **REPRODUCED** |

---

## P1 — Auditability

### F-AUD-01 — Input file content hashing absent

| Field | Value |
|---|---|
| **Finding ID** | F-AUD-01 |
| **Severity** | P1 |
| **Affected module** | `evidence.py`, `pipeline.py` |
| **Evidence** | ADV-HASH-01: `evidence.py` source contains no `hash`/`sha` tokens. Evidence records basename only. |
| **Business impact** | Cannot prove which bytes were processed; file rename/reuse breaks chain of custody. |
| **Reproduction steps** | Static review of `build_success_evidence` / `build_failure_evidence`. |
| **Recommended fix** | SHA-256 of input bytes (+ optional output hashes) in evidence. |
| **Regression test** | Changing one CSV byte changes evidence hash. |
| **Verification status** | **CONFIRMED** (control **NOT FOUND**) |

### F-AUD-02 — JSONL evidence incomplete for financial attestation

| Field | Value |
|---|---|
| **Finding ID** | F-AUD-02 |
| **Severity** | P1 |
| **Affected module** | `evidence.py` |
| **Evidence** | Missing: input hash, amount totals, reject-reason histogram, schema fingerprint, package version, config hash. Present: counts, quality_score, output basenames, run_id, timestamp. |
| **Business impact** | Evidence supports operational replay counts more than financial sign-off. |
| **Reproduction steps** | ADV-REC-01 key inventory. |
| **Recommended fix** | Expand schema; version the evidence record (`evidence_schema_version`). |
| **Regression test** | Contract test for required attestation fields. |
| **Verification status** | **CODE-INDICATED** |

### F-AUD-03 — Report content determinism vs audit identity non-determinism

| Field | Value |
|---|---|
| **Finding ID** | F-AUD-03 |
| **Severity** | P2/P1 nuance |
| **Affected module** | `evidence.py` (`uuid`, `timestamp`), reporting |
| **Evidence** | DET-SUMMARY / DET-QUALITY-CSV: same input → identical summary JSON and quality CSV bytes. `run_id` differs each run (expected for audit uniqueness). Fixed output filenames overwrite prior run artifacts. |
| **Business impact** | Metrics are reproducible; artifact history is not versioned on disk (only JSONL append preserves run history metadata). |
| **Reproduction steps** | Dual `run_pipeline` in temp dirs (DET-* probes). |
| **Recommended fix** | Optional `run_id`-scoped output directories; retain overwrite behavior as opt-in. |
| **Regression test** | Byte-identical reports for fixed synthetic input (already informally proven). |
| **Verification status** | **REPRODUCED** |

### F-AUD-04 — Rejected transactions are written and counted (control)

| Field | Value |
|---|---|
| **Finding ID** | F-AUD-04 |
| **Severity** | Informational (positive) |
| **Affected module** | `reporting.py`, `pipeline.py`, `cleaning.py` |
| **Evidence** | `rejected_rows.xlsx` always written; evidence `rejected_rows` / `duplicates_removed`; tests cover success/failure evidence. |
| **Business impact** | Supports quarantine accountability at row level. |
| **Reproduction steps** | Existing pytest + sample run. |
| **Recommended fix** | Add amount totals per reject reason. |
| **Regression test** | Extend existing pipeline tests. |
| **Verification status** | **REPRODUCED** |

---

## P2 — Commercial readiness

### F-COM-01 — No LICENSE file

| Field | Value |
|---|---|
| **Finding ID** | F-COM-01 |
| **Severity** | P2 |
| **Affected module** | Repository root |
| **Evidence** | `LICENSE` path does not exist. README “License / data note” only covers synthetic data warning. |
| **Business impact** | Unclear redistribution rights for commercial reuse. |
| **Reproduction steps** | Check for `LICENSE*`. |
| **Recommended fix** | Add SPDX license; document third-party notices (pandas BSD, openpyxl MIT). |
| **Regression test** | CI check for LICENSE presence. |
| **Verification status** | **CONFIRMED** |

### F-COM-02 — Documentation overclaims relative to float/FX/qty behavior

| Field | Value |
|---|---|
| **Finding ID** | F-COM-02 |
| **Severity** | P2 |
| **Affected module** | `README.md` L75–84 (“No silent data loss”), architecture |
| **Evidence** | Row partition holds, but amount-level silent risk exists (F-FIN-01/03/05). |
| **Business impact** | Portfolio/commercial readers may over-trust controls. |
| **Reproduction steps** | Compare README principles to F-FIN-* findings. |
| **Recommended fix** | Narrow claim to “no silent **row** loss”; document money/FX limitations. |
| **Regression test** | Doc lint / architecture checklist. |
| **Verification status** | **CODE-INDICATED** |

### F-COM-03 — Unpinned dependencies / no lockfile

| Field | Value |
|---|---|
| **Finding ID** | F-COM-03 |
| **Severity** | P2 |
| **Affected module** | `requirements.txt`, `pyproject.toml` |
| **Evidence** | Lower bounds only; no `uv.lock`/`poetry.lock`/`requirements.lock`. |
| **Business impact** | Non-reproducible installs; complicates audit replay. |
| **Reproduction steps** | Manifest inspection. |
| **Recommended fix** | Pin + lock; document Python 3.12 baseline. |
| **Regression test** | Install from lock in CI. |
| **Verification status** | **CONFIRMED** |

### F-COM-04 — Test suite coverage gaps vs audit objectives

| Field | Value |
|---|---|
| **Finding ID** | F-COM-04 |
| **Severity** | P2 |
| **Affected module** | `tests/*` |
| **Evidence** | 15 tests, all passed; no tests for Decimal money, FX, formula injection, hashing, amount reconciliation, negative amount policy, monthly totals edge cases, evidence schema contract. See `TEST_COVERAGE_GAPS.md`. |
| **Business impact** | Regressions in P0 areas may ship unnoticed. |
| **Reproduction steps** | Inventory tests vs objectives. |
| **Recommended fix** | Prioritized tests in remediation plan. |
| **Regression test** | Coverage gate for critical modules. |
| **Verification status** | **CONFIRMED** |

---

## Explicit NOT FOUND / NOT VERIFIED summary

| Item | Status |
|---|---|
| Hardcoded credentials | **NOT FOUND** |
| Outbound network/upload code | **NOT FOUND** |
| Input/output cryptographic hashing | Control **NOT FOUND** |
| Revenue/expense classifier | Capability **NOT FOUND** |
| Dependency CVE results | **NOT VERIFIED** |
| Production DB / private-repo access | Not attempted (constraint) |
| Destructive filesystem tests outside temp | Not performed (constraint) |
