# Remediation Plan — Financial Data Automation

**Audit date:** 2026-11-09  
**Constraint reminder:** This plan is advisory. The audit itself did **not** modify application source, commit, push, or deploy.

## Goal

Reach a minimal, evidence-backed posture where:

1. Monetary totals are exact under a declared rounding policy.  
2. Every input amount is reconciled to clean + reject buckets.  
3. Untrusted Excel/CSV cannot emit executable formulas.  
4. Audit JSONL can support chain-of-custody (hash + schema).  
5. Docs/license/deps match commercial honesty.

---

## Minimal remediation sequence (do in order)

### Phase 0 — Safety baseline (½–1 day)

| Step | Action | Closes / reduces | Exit criteria |
|---|---|---|---|
| 0.1 | Run `pip-audit` (or OSV) on locked env; record results | R-P0-08 | CVE report attached; criticals triaged |
| 0.2 | Add `LICENSE` + third-party notice | R-P2-01 | SPDX file present |
| 0.3 | Pin deps + commit lockfile | R-P2-03 | Reproducible install in CI |
| 0.4 | Soften README claim to “no silent **row** loss”; list money/FX limits | R-P2-02 | Docs match known residual risk |

*No application behavior change required beyond docs/license/pins.*

### Phase 1 — P0 financial + Excel safety (2–4 days)

| Step | Action | Findings | Exit criteria |
|---|---|---|---|
| 1.1 | Introduce monetary type (`Decimal` or integer cents) end-to-end for `amount`/`cost`/`unit_price` | F-FIN-01 | ADV-FLOAT-01 style test passes |
| 1.2 | Emit `input_amount_total`, `clean_amount_total`, `rejected_amount_total`, `amount_variance` in evidence; fail pipeline if variance ≠ 0 under policy | F-FIN-02, F-AUD-02 | Reconciliation test green |
| 1.3 | Quarantine `inconsistent_quantity_price` (or make severity configurable default=reject) | F-FIN-03 | ADV-QTY-01 becomes reject |
| 1.4 | Neutralize Excel/CSV formula prefixes on all string exports | F-SEC-01, F-VAL-01 | ADV-XLSX-01 neutralized |
| 1.5 | Declare and implement duplicate retention policy (document + code); record discarded payload in rejects | F-FIN-04 | Policy test green |
| 1.6 | Single-currency enforcement **or** per-currency totals (no silent cross-sum) | F-FIN-05 | ADV-FX-01 fails closed / grouped |
| 1.7 | Signed-amount / revenue-expense policy (even if v1 = “allow negatives but label”) | F-FIN-06, F-VAL-04 | Policy matrix tested |

**Stop-ship for “financial demo claims” until 1.1–1.4 land.**

### Phase 2 — P1 auditability (1–2 days)

| Step | Action | Findings | Exit criteria |
|---|---|---|---|
| 2.1 | SHA-256 of input file bytes in success/failure evidence | F-AUD-01 | Hash changes when byte changes |
| 2.2 | Optional output hashes; `evidence_schema_version`; package `__version__` | F-AUD-02 | Schema contract test |
| 2.3 | Align blank amount → `missing_amount` reject reason; keep `invalid_amount` for parse failures | F-VAL-05 | BLANK-AMT metrics agree |
| 2.4 | Reject-reason amount histogram in quality report + evidence | F-AUD-04 extension | Rollup test |
| 2.5 | Optional `run_id` output subdirectory to avoid overwrite | F-AUD-03 | Prior artifacts retained when enabled |
| 2.6 | Document amount grammar (`$`, commas, locales) | F-VAL-03 | Fixture table |

### Phase 3 — P1 path/privacy hardening (½–1 day)

| Step | Action | Findings | Exit criteria |
|---|---|---|---|
| 3.1 | Strict path mode: confine reads/writes under project root | F-SEC-05 | Outside-root write denied |
| 3.2 | Return relative output paths from pipeline/CLI | F-SEC-05 / ADV-PATH-01 | No drive-letter leakage in default CLI |
| 3.3 | Evidence/PII contract test (no customer/description in JSONL) | F-SEC-04 | Test green |

### Phase 4 — Test & ops hardening (1–2 days)

| Step | Action | Gaps | Exit criteria |
|---|---|---|---|
| 4.1 | Promote audit probes into `tests/` (money, FX, formula, hash, reconcile) | G-FIN-*, G-SEC-06, G-AUD-* | CI green |
| 4.2 | Add `compute_monthly_totals` + CLI exit-code tests | G-COM-04/05 | Coverage of reporting path |
| 4.3 | Malformed CSV/XLSX matrix (non-destructive temp only) | G-VAL-01/02 | Explicit expected errors |
| 4.4 | CI: pytest + pip-audit + secret scan | G-SEC-01/05 | Required checks |

---

## Decision rules (Claim → Evidence → Verification → Decision)

| Claim you want to make | Required closed risks | Decision if open |
|---|---|---|
| “No silent data loss” | R-P0-01..06 + row partition | **Do not claim** — say “no silent row loss” only |
| “Audit-ready evidence” | R-P1-01, R-P1-02 + Phase 2 | **Do not claim** chain-of-custody |
| “Safe for untrusted Excel” | R-P0-07 | **Do not claim** |
| “Commercial-ready package” | R-P2-01..03 + CVE scan | **Do not claim** until Phase 0+ CVE |
| “Local trusted operator demo” | Current controls C-01..C-10 | **Acceptable** with documented residual P0 risks |

---

## Suggested fix sketches (non-implementing)

### Money (F-FIN-01)

- Parse amounts with a dedicated parser → `Decimal` quantized to `0.01` (or configurable scale).  
- Aggregations use `sum(..., start=Decimal('0'))`; serialize as string/fixed scale in Excel.

### Reconciliation (F-FIN-02)

```text
variance = input_total - (clean_total + rejected_total)
assert abs(variance) <= money_epsilon  # ideally 0 for Decimal
```

### Formula neutralization (F-SEC-01)

- For each string cell value matching `^[=+\-@]`, prefix with `'` or replace leading character per OWASP CSV/Excel guidance before `to_excel`/`to_csv`.

### Hashing (F-AUD-01)

- `hashlib.sha256(Path(input_file).read_bytes()).hexdigest()` into evidence at start of run (before mutate).

---

## Explicit non-goals for minimal path

- Database, cloud upload, authN/Z, multi-tenant SaaS hardening  
- Full FX engine (grouping/fail-closed is enough for v1)  
- ML quality scoring  
- Changing sample synthetic customer names (already non-production)

---

## Verification checklist after implementation (future work)

- [ ] `pytest` includes new P0 tests; all green  
- [ ] Re-run ADV-FLOAT/QTY/XLSX/FX/OMIT probes → expected mitigated outcomes  
- [ ] Evidence JSONL schema contract validated  
- [ ] `pip-audit` clean or waived with ticket IDs  
- [ ] README claims match residual risk register  

---

## Final prioritized register (executive)

| Priority | Risks | Minimal sequence phase |
|---|---|---|
| **P0** | R-P0-01 … R-P0-08 | Phase 0.1 + Phase 1 |
| **P1** | R-P1-01 … R-P1-07 | Phase 2–3 |
| **P2** | R-P2-01 … R-P2-04 | Phase 0.2–0.4 + Phase 4 |

**Bottom line:** The repository is a solid **local, transparent DQ demo** with good row-quarantine and evidence scaffolding. It is **not yet** ready for financial attestation or untrusted spreadsheet intake without Phase 1 remediations.
