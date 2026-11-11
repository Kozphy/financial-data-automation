# Financial Data Quality & Audit Automation — P0–P2 roadmap

Scope: local-first, synthetic data only, no claims of certification or production attestation.

## P0 — stop misleading financial conclusions
- [x] Add post-ingestion row/amount bridge (input = clean + quarantined), fail on variance; disclose unparseable inputs.
- [x] Hash input bytes and output artifacts, include schema version and explicit limitations in evidence.
- [x] Add adversarial regression tests for row conservation, amount mutation, quarantined values, and artifact tampering.
- [ ] **Open:** end-to-end Decimal/integer minor-unit parsing and currency-specific scale rules; current reconciliation starts *after* pandas parsing.
- [ ] **Open:** fail-closed mixed-currency handling; no cross-currency financial totals without FX policy.
- [ ] **Open:** reject quantity × unit price mismatches; explicit duplicate resolution and sign policies.
- [ ] **Open:** Excel/CSV formula-injection protection on exported strings; safe read/write of hostile files.

## P1 — traceability and operational reliability
- [ ] Run-scoped atomic outputs and crash-safe event writing; concurrent runs must not share output paths.
- [ ] Evidence schema validation, run/record chaining or signed remote attestations, custody and retention controls.
- [ ] Reject-reason histograms and explicit control decisions (PASS/WARN/BLOCK).
- [ ] Idempotent reruns, stable input schema profiles, redaction/privacy safeguards, and CLI exit-code tests.
- [ ] Automated CI (pytest, security audit, secret scanning) and coverage metrics.

## P2 — enterprise integration
- [ ] Configurable chart-of-accounts mapping, reconciliation to bank/GL control totals, FX-rate provenance.
- [ ] Role-based review/approval workflow, segregation of duties, audit export and evidence storage.
- [ ] Batch orchestration, operational metrics, performance/load tests, versioned deployment workflows.
- [ ] Commercial documentation, supported data contracts and onboarding, licensing and dependency lockfiles.

## Evidence and claims
- New `reconciliation` figures are `Decimal(str(value))` computed on *ingested* values. A source value already rounded by pandas cannot be recovered. An unparseable amount produces a **partial** monetary reconciliation even when row conservation holds.
- SHA-256 checks are integrity comparisons against an independently trusted record. Local editable JSONL is **not** an immutable ledger, and hashes do not authenticate a person.
- Current outputs still overwrite deterministic paths. Do not run concurrent jobs targeting the same folder.
- Do not describe the project as enterprise-certified, bank/GL-reconciled, tamper-proof or ready for sensitive client data.
