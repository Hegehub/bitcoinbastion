# Roadmap (reality-aligned, 2026-04-30)

This roadmap reflects **current implemented state** and remaining gaps to production-grade finalization.
It intentionally separates what is already delivered vs what is still partial.

## Current readiness snapshot
- Bastion core: **~92%**
- Citadel: **~84%**
- Bitcoin protocol maturity: **~82%**
- Explainability E2E: **~86%**
- Operations hardening: **~88%**
- Overall finalization: **~89%**

---

## Phase 1 — Truth & integrity (Mostly completed)
### Delivered
- Model/migration table parity check in repo tooling.
- Docs truthfulness checks (routes/models/core docs heading) wired into smoke flow.
- Status/readiness docs normalized to audit-style language.

### Remaining
- Add deeper schema parity checks (constraints/defaults/indexes), not only table-level coverage.
- Enforce stricter doc release gates for roadmap/status drift.

---

## Phase 2 — Runtime reliability (Partially completed)
### Delivered
- Signal deduplication with source identity paths.
- Delivery retry/cooldown guards and failure logging.
- Recovery SLO/drill metadata surfaced through admin/observability.

### Remaining
- Close remediation loop automation (detect → auto-action → verification).
- Add stronger circuit-breaker behavior for persistent delivery/provider failures.

---

## Phase 3 — Protocol depth (Partially completed)
### Delivered
- UTXO/mempool/script/descriptor analysis integrated into key service outputs.
- Chain-state/finality/reorg context exposed and consumed at baseline level.

### Remaining (critical)
- Production calibration for finality/reorg and fee-market stress behavior.
- Provider realism hardening (less fallback/default behavior in critical paths).
- Better live-data backtesting windows for protocol scoring confidence.

---

## Phase 4 — Citadel realism (Partially completed)
### Delivered
- Weighted multi-domain scoring with explainability and coverage guarantees.
- Topology/simulation/recovery/inheritance flows are implemented and connected.
- Runtime wallet context now participates in assessment shaping.

### Remaining (critical)
- Remove remaining synthetic assumptions in recovery/inheritance/context fallbacks.
- Strengthen data provenance guarantees for every score component.
- Add deterministic calibration validation suite (golden scenarios + drift thresholds).

---

## Phase 5 — Explainability closure (Advanced, not final)
### Delivered
- Cross-domain explainability payloads are present for high-impact outputs.
- Score inputs/weights and domain sections are exposed in assessment output.

### Remaining
- Full path-level traceability for all high-impact decisions (input → transform → policy impact → output).
- Add explainability regression gates in CI for contract stability and completeness.

---

## Phase 6 — Production lock-in (In progress)
### Delivered
- Release-time production readiness checklist format.
- Final production audit document with explicit pass/partial assessments.

### Remaining (release blockers)
1. Finalize protocol calibration and prove stability on live-like traffic windows.
2. Close remaining synthetic fallback branches in Citadel critical scoring paths.
3. Complete recovery remediation automation and verification loop.
4. Run final release audit with objective gates and sign-off evidence.

---

## Immediate next execution queue
1. **Protocol calibration pack**: finality/reorg + mempool stress backtesting + threshold tuning.
2. **Citadel realism pack**: eliminate residual synthetic recovery/inheritance assumptions.
3. **Ops closure pack**: auto-remediation workflows with post-action validation.
4. **Release gate pack**: objective production audit checklist runbook with artifacts.


## Block M0 — Mining Sovereignty Intelligence Foundation (new)
### Delivered in M0
- Domain architecture and boundary definition finalized.
- Draft schema contracts added for mining sovereignty intelligence (no DB tables/migrations).
- Integration sequencing documented across On-chain, Signals, Policy, Explainability, and Citadel.

### Next
- M1: provider abstraction and read-only scoring/API path.
- M2: persistence + scheduled ingestion.
- M3: full weighted integration and calibration.
