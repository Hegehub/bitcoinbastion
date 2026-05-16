# Status (docs truth audit)

Audit date: **2026-05-15**

This document reflects repository state from code and tests, not roadmap targets.

## Capability status

### API platform
- **IMPLEMENTED**: FastAPI route surface for auth, users, news, signals, entities, on-chain, wallet, fees, privacy, treasury, policy, citadel, observability, admin.

### Services
- **IMPLEMENTED**: service modules exist across ingestion, scoring, policy, wallet, treasury, observability, citadel, delivery, and auth.
- **BASELINE**: several service outputs are heuristic or limited-depth.

### Models and persistence
- **IMPLEMENTED**: SQLAlchemy model set exists and is migrated by Alembic revisions.
- **IMPLEMENTED**: migration replay and deterministic schema recreation smoke test exists.

### Runtime governance and observability
- **IMPLEMENTED**: `/api/v1/observability/snapshot` includes runtime severity model, degraded mode semantics, and operational evidence packet.
- **IMPLEMENTED**: runtime telemetry gauges expose severity score, degraded mode active, provider share, delivery failures, unresolved recovery findings, and citadel runtime health.
- **BASELINE**: threshold tuning for paging/escalation remains environment-specific and should be validated per deployment.

### Synthetic/baseline areas
- **SYNTHETIC**: parts of Citadel dependency/simulation behavior.
- **BASELINE**: Telegram runtime behavior, some Bitcoin protocol-depth analyzers, and explainability depth.

## Evidence-backed constraints
- No production SLO attainment is claimed in this file.
- No completion percentages are used.
- Readiness claims remain in checklist form in `docs/PRODUCTION_READINESS.md`.

## Protocol maturity truth (P5)
- **IMPLEMENTED**: Chain-state, mempool, UTXO, and provider outputs expose source-quality metadata (`source_type`, `provider_name`, fallback/mock flags, freshness, confidence, limitations).
- **IMPLEMENTED**: Operational evidence packets summarize runtime risk, degraded dependencies, recovery/drill status, delivery health, and provider quality for operator workflows.
- **BASELINE**: Mempool/UTXO/script analyzers remain deterministic over caller-provided snapshots/hints and are not full node-level verification.
- **SYNTHETIC**: Citadel scenario simulations and some protocol stress inputs remain deterministic synthetic models.
- **Constraint**: Protocol and runtime confidence values are operational heuristics and must not be interpreted as consensus/finality guarantees.
