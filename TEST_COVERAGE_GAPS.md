# Test Coverage Gaps — Financial Data Automation

**Audit date:** 2026-11-09  
**Baseline executed:** `pytest -v` → **15 passed** (2.27s) — claims below distinguish *existing coverage* from *gaps*.

## Current suite map

| Test file | Cases | What is covered |
|---|---|---|
| `tests/test_ingestion.py` | 5 | Column normalize; CSV/XLSX load; missing file; unsupported suffix |
| `tests/test_validation.py` | 4 | Missing columns; invalid date; invalid amount; duplicate id count |
| `tests/test_cleaning.py` | 1 | Reject reasons + row partition on mixed bad rows |
| `tests/test_analytics.py` | 2 | Happy-path summary + quality score edge (0 inputs) |
| `tests/test_pipeline.py` | 3 | Success evidence; duplicate counts; failure evidence |

**Not present as first-class modules/tests:** evidence unit tests, reporting unit tests, formula injection, Decimal money, FX, hashing, amount reconciliation, monthly totals, negative amount policy, CLI tests.

---

## Gaps by audit objective

### P0 — Financial correctness

| Gap ID | Objective | Current coverage | Gap | Suggested adversarial test |
|---|---|---|---|---|
| G-FIN-01 | Floating-point / rounding | None | No Decimal/cent fixtures | `test_monetary_sum_exact_cents` — 0.1+0.2+0.3 / many 0.01 rows |
| G-FIN-02 | Input vs output totals | None | No bridge assertion | `test_amount_reconciliation_evidence` |
| G-FIN-03 | Quarantine of qty×price mismatch | Counted in validation only | Not asserted quarantined | `test_inconsistent_qty_price_rejected` (ADV-QTY-01) |
| G-FIN-04 | Duplicate retention policy | Counts duplicates | No “later correction wins” case | `test_duplicate_keeps_policy_latest` |
| G-FIN-05 | Multi-currency | None | Silent sum untested | `test_mixed_currency_fails_or_groups` |
| G-FIN-06 | Sign / revenue-expense | None | Negative amount accepted untested | `test_negative_amount_policy` |
| G-FIN-07 | Silent transform changes | Partition only | No type/coercion delta ledger | `test_coercion_changes_are_evidenced` |

### P0 — Privacy / security

| Gap ID | Objective | Current coverage | Gap | Suggested adversarial test |
|---|---|---|---|---|
| G-SEC-01 | Secrets | None | No secret-scan CI | `detect-secrets` / gitleaks in CI |
| G-SEC-02 | PII in evidence | Pipeline asserts no `Users` in JSON | Does not assert absence of customer/description | `test_evidence_excludes_row_payloads` |
| G-SEC-03 | Path safety | Relative path intent in CLI display | No allowlist tests | `test_refuse_write_outside_root` |
| G-SEC-04 | Network calls | None | No import allowlist test | `test_no_network_imports` |
| G-SEC-05 | Dependency CVEs | None | `pip-audit` not run | CI `pip-audit` job |
| G-SEC-06 | Excel formula injection | **None** | Critical gap | `test_excel_formula_prefix_neutralized` (ADV-XLSX-01) |

### P1 — Excel / validation

| Gap ID | Objective | Current coverage | Gap | Suggested adversarial test |
|---|---|---|---|---|
| G-VAL-01 | Malformed CSV | Basic happy CSV | BOM, delim, embedded newlines, empty file | `test_malformed_csv_matrix` |
| G-VAL-02 | Malformed XLSX | Happy path | Multi-sheet pick, empty sheet, corrupt zip | `test_xlsx_edge_matrix` |
| G-VAL-03 | Column mapping | Missing required fails | Synonym/alias not defined | Document + `test_alias_map` if added |
| G-VAL-04 | Duplicate detection | Yes (count + pipeline) | Near-duplicates (whitespace id) | `test_transaction_id_normalize_before_dedupe` |
| G-VAL-05 | Exception handling | Failure evidence test | Partial mid-write failure | Fault-injection around `to_excel` |
| G-VAL-06 | Revenue/expense | None | Capability absent | Add when feature exists |
| G-VAL-07 | Blank vs invalid amount metrics | None | Metric mismatch untested | BLANK-AMT probe as unit test |

### P1 — Auditability

| Gap ID | Objective | Current coverage | Gap | Suggested adversarial test |
|---|---|---|---|---|
| G-AUD-01 | Input hashing | None | Feature absent | `test_evidence_includes_sha256` |
| G-AUD-02 | JSONL completeness | Success/fail smoke | No schema contract | `test_evidence_schema_required_keys` |
| G-AUD-03 | Deterministic reports | Indirect | No byte-equality test | DET-QUALITY-CSV as formal test |
| G-AUD-04 | Rejected accounted for | Row partition + counts | No amount-by-reason | `test_reject_reason_amount_rollup` |
| G-AUD-05 | Evidence append integrity | Single-line asserts | Concurrent/multi-run append | Two-run append length=2 |

### P2 — Commercial readiness

| Gap ID | Objective | Current coverage | Gap | Suggested check |
|---|---|---|---|---|
| G-COM-01 | Licensing | None | No LICENSE | Presence test / policy |
| G-COM-02 | Docs accuracy | None | Overclaim vs behavior | Doc checklist review |
| G-COM-03 | Operational safeguards | verify_outputs existence only | No disk-full, permission, lock tests | SRE chaos light |
| G-COM-04 | `compute_monthly_totals` | Untested module function | Zero direct tests | Month boundary / TZ-naive dates |
| G-COM-05 | CLI `run_pipeline.py` | Untested | Exit codes / usage | `test_cli_exit_codes` |

---

## Adversarial cases executed this audit (not committed)

These were run via temp scripts only (read-only constraint — **not** added under `tests/`).

| Probe ID | Outcome | Maps to |
|---|---|---|
| ADV-FLOAT-01 | REPRODUCED float sum ≠ 0.6 | G-FIN-01 |
| ADV-QTY-01 | REPRODUCED mismatch kept | G-FIN-03 |
| ADV-XLSX-01 | REPRODUCED formula string export | G-SEC-06 |
| ADV-DUP-01 | REPRODUCED keep-first | G-FIN-04 |
| ADV-FX-01 | REPRODUCED mixed FX sum | G-FIN-05 |
| ADV-PART-01 | Partition OK | Control C-01 |
| ADV-MAP-01 | Fail closed OK | Control C-06 |
| ADV-HASH-01 | Hash control absent | G-AUD-01 |
| ADV-AMT-01 | `$12.50` rejected | G-VAL / F-VAL-03 |
| ADV-OMIT-01 | No amount bridge | G-FIN-02 |
| NEG-AMT | Negative kept | G-FIN-06 |
| BLANK-AMT | Metric mismatch | G-VAL-07 |
| DET-* | Metrics deterministic; run_id not | G-AUD-03 |

---

## Coverage priority for remediation

1. **Must-add before financial claims:** G-FIN-01, G-FIN-02, G-FIN-03, G-SEC-06  
2. **Must-add before untrusted Excel intake:** G-SEC-06, G-VAL-01/02  
3. **Must-add before audit sign-off:** G-AUD-01, G-AUD-02, G-AUD-04  
4. **Should-add for ops:** G-COM-04, G-COM-05, G-SEC-05  
