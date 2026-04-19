# Roadmap

This roadmap follows the repository's master prompt structure and maps it onto practical delivery phases.

## Phase A — Foundation
- Harden config, logging, exceptions, and app wiring.
- Maintain DB migration hygiene and reproducibility checks.
- Keep Docker/compose + Make targets deploy-ready.

## Phase B — Core Intelligence
- Expand news ingestion and article normalization.
- Improve deduplication/clustering and explainable scoring.
- Strengthen baseline signal generation + publish workflow.
- Extend health/news/signals APIs and task orchestration.

## Phase C — Sovereign / Treasury / Privacy
- Deepen auth and user-subscription workflows.
- Expand wallet health + fee exposure analysis.
- Improve treasury request + PSBT metadata lifecycle.
- Add stronger privacy scoring and watchlist intelligence.

## Phase D — Future-Critical Layer
- Mature on-chain provider abstraction and detectors.
- Expand entity confidence and provenance tracking.
- Advance policy-as-code runtime and recommendation engine.
- Grow evidence graph and multi-horizon interpretation.

## Phase E — Hardening / Deploy
- Complete observability coverage (metrics, traces-ready abstractions, job telemetry).
- Add CI quality gates for migrations/contracts.
- Finalize readiness checks, deployment playbooks, and production runbooks.

## Immediate next focus
1. Improve contract tests for integrations (`rss`, `bitcoin provider`).
2. Strengthen signal explainability payload for cross-source evidence narratives.
3. Expand policy execution visibility for treasury-sensitive flows (execution summary endpoint delivered; continue dashboard-level aggregation).
