# Risk Register — Financial Data Automation

**Audit date:** 2026-11-09  
**Source:** `AUDIT_FINDINGS.md`  
**Ordering:** Severity (P0 → P1 → P2), then residual financial/security impact  

| Risk ID | Sev | Title | Finding IDs | Likelihood | Impact | Residual risk | Owner suggestion | Verification |
|---|---|---|---|---|---|---|---|---|
| R-P0-01 | P0 | Monetary float precision errors in totals | F-FIN-01 | High (any non-cent-aligned inputs) | High (misstated totals) | Open | Data Quality + FinEng | REPRODUCED |
| R-P0-02 | P0 | No amount reconciliation between input, clean, reject | F-FIN-02, F-AUD-02 | High | High (unauditable P&L bridge) | Open | FinSys Auditor + SRE | REPRODUCED |
| R-P0-03 | P0 | Qty×price mismatches enter cleaned ledger | F-FIN-03 | Medium | High (wrong line economics) | Open | Data Quality | REPRODUCED |
| R-P0-04 | P0 | Duplicate ID keep-first retains wrong amount | F-FIN-04 | Medium | High (missed corrections) | Open | FinSys Auditor | REPRODUCED |
| R-P0-05 | P0 | Cross-currency amounts aggregated as one unit | F-FIN-05 | Medium (if multi-currency used) | High (false totals) | Open | FinEng | REPRODUCED |
| R-P0-06 | P0 | Negative amounts / no revenue-expense policy | F-FIN-06, F-VAL-04 | Medium | High (sign/class errors) | Open | FinEng | REPRODUCED |
| R-P0-07 | P0 | Excel formula injection on export | F-SEC-01, F-VAL-01 | Medium (untrusted inputs) | High (client-side code exec risk) | Open | AppSec | REPRODUCED |
| R-P0-08 | P0 | Dependency CVE posture unknown | F-SEC-06, F-COM-03 | Unknown | Potentially High | Open | SRE / SecOps | NOT VERIFIED |
| R-P1-01 | P1 | Missing input SHA-256 chain of custody | F-AUD-01 | High (every run) | Medium (weak evidence) | Open | SRE / GRC | CONFIRMED |
| R-P1-02 | P1 | Evidence schema incomplete for attestation | F-AUD-02 | High | Medium | Open | GRC | CODE-INDICATED |
| R-P1-03 | P1 | Blank vs invalid amount metric mismatch | F-VAL-05 | Medium | Medium (metric distrust) | Open | Data Quality | REPRODUCED |
| R-P1-04 | P1 | Currency-symbol / locale amount parsing gaps | F-VAL-03 | Medium | Medium (over-quarantine) | Open | Data Quality | REPRODUCED |
| R-P1-05 | P1 | Unrestricted path write / absolute path return | F-SEC-05 | Low (local CLI) / High (if service-wrapped) | Medium | Open | AppSec | REPRODUCED |
| R-P1-06 | P1 | Output workbooks hold business fields (by design) | F-SEC-04 | High if real data used | Medium–High | Accepted with controls | Privacy | CODE-INDICATED |
| R-P1-07 | P1 | Overwrite of fixed output filenames loses prior artifacts | F-AUD-03 | Medium | Medium | Open | SRE | REPRODUCED |
| R-P2-01 | P2 | No LICENSE / unclear commercial terms | F-COM-01 | High | Medium (legal) | Open | Legal / Owner | CONFIRMED |
| R-P2-02 | P2 | Docs overclaim “no silent data loss” | F-COM-02 | High | Low–Medium (trust) | Open | Product | CODE-INDICATED |
| R-P2-03 | P2 | Unpinned deps / no lockfile | F-COM-03 | High | Medium | Open | SRE | CONFIRMED |
| R-P2-04 | P2 | Missing adversarial/financial regression tests | F-COM-04 | High | Medium | Open | QA | CONFIRMED |

## Controls observed (risk reducers)

| Control ID | Description | Finding | Status |
|---|---|---|---|
| C-01 | Cleaned + rejected row partition (no silent row drop) | F-FIN-07 | Effective for rows |
| C-02 | Reject workbook + reject_reason | F-AUD-04 | Effective |
| C-03 | Append-only JSONL evidence with run_id | pipeline/evidence | Partial |
| C-04 | Input basename sanitization in evidence | evidence.sanitize_input_name | Effective |
| C-05 | Missing/unsupported formats fail closed | ingestion/validation | Effective |
| C-06 | Wrong column names fail closed | F-VAL-02 | Effective |
| C-07 | No hardcoded secrets found | F-SEC-02 | Effective (absence) |
| C-08 | No network client imports found | F-SEC-03 | Effective (absence) |
| C-09 | Deterministic summary/quality CSV for fixed input | F-AUD-03 | Effective for metrics |
| C-10 | Existing pytest suite (15/15 passed) | execution log | Baseline only |

## Risk heat (summary)

```text
P0 open: 8
P1 open: 7
P2 open: 4
Positive controls documented: 10
```

## Prioritized attention order

1. R-P0-01 / R-P0-02 — money precision + reconciliation (blocks financial sign-off)  
2. R-P0-07 — Excel injection (blocks untrusted-file handling)  
3. R-P0-03 / R-P0-04 / R-P0-05 / R-P0-06 — transformation correctness  
4. R-P0-08 — dependency audit (unblock with scanner)  
5. R-P1-01 / R-P1-02 — evidence hardening  
6. R-P2-* — license, docs, pins, tests  
