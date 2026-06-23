# Roadmap and Backlog

This consolidated roadmap merges the previous `ROADMAP.md`, `BACKLOG_MASTER.md`, `TECHNICAL_DEBT.md` and `RC_FREEZE.md` documents. It tracks project readiness, upcoming tasks, technical debt and release policies.

## Current Readiness

- Bastion core readiness: ~92%
- Citadel: ~84%
- Bitcoin protocol maturity: ~82%
- Explainability end‑to‑end: ~86%
- Operations hardening: ~88%
- Overall finalisation: ~89%

## Phases and Progress

### Phase 1 — Truth & Integrity

Delivered items include migration/model parity checks, docs truthfulness checks and normalised status language. Remaining work focuses on deeper schema parity checks and stricter documentation release gates.

### Phase 2 — Runtime Reliability

Delivered items include signal deduplication, delivery retry/cooldown guards and recovery drill metadata. Remaining tasks include closing the remediation loop and adding circuit‑breaker behaviours for persistent failures.

### Phase 3 — Protocol Depth

Delivered features cover UTXO/mempool/script/descriptor analysis and baseline chain‑state context. Critical remaining tasks include calibrating finality/reorg and fee‑market behaviour, hardening provider realism and improving backtesting windows.

### Phase 4 — Citadel Realism

Delivered progress includes weighted multi‑domain scoring and runtime context integration. Critical remaining items involve removing synthetic assumptions, strengthening data provenance and adding calibration validation.

### Phase 5 — Explainability Closure

Delivered progress covers cross‑domain explainability payloads and exposure of score inputs and weights. Remaining tasks include full traceability from input to output and explainability regression gates.

### Phase 6 — Production Lock‑In

Delivered steps include a release‑time checklist and final production audit format. Release blockers include final protocol calibration, closing synthetic branches, completing recovery automation and running the final release audit.

## Backlog Tasks

Backlog items are organised by phase and labelled `BKL‑xx`. Highlights include:

- **BKL‑01/02/03:** Align migration history and schema truth, and correct status docs.
- **BKL‑04/05/06:** Finalise signal orchestration, Telegram delivery and recovery retries.
- **BKL‑07/08/09/10/11:** Deepen UTXO, mempool, fee‑market, chain‑state, provider realism and descriptor awareness.
- **BKL‑12..16:** Replace synthetic Citadel inputs, upgrade dependency topology, disaster simulation realism, verification semantics and repair prioritisation.
- **BKL‑17/18:** Close explainability traceability and finalise policy governance.
- **BKL‑19/20:** Close automated drills and run the final production readiness pass.

## Technical Debt

The technical debt registry categorises outstanding issues:

- **Production blockers:** missing calibration evidence and staging/production deployment evidence.
- **Intentional placeholders:** enterprise governance/observability stack placeholders and Kubernetes/Helm templates requiring adaptation.
- **Non‑blocking polish:** frontend lint warnings, accessibility certification and full E2E coverage.
- No critical TODO/FIXME markers were found in runtime code paths.

## RC Freeze Policy

During a release‑candidate freeze, only critical bug fixes, security fixes and documentation corrections are allowed; major features, schema or architecture rewrites and large dependency changes are disallowed. All RC changes require manual sign‑off and a documented rollback expectation.

## Immediate Next Queue

The immediate next tasks include final protocol calibration, elimination of synthetic Citadel assumptions, automation closure for recovery operations and a final release audit.
