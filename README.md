# Bitcoin Bastion

Bitcoin Bastion is a FastAPI backend for Bitcoin-focused monitoring, policy workflows, and sovereignty assessments.

## Repository scope
- API endpoints under `app/api/v1`.
- Service orchestration under `app/services`.
- SQLAlchemy models under `app/db/models`.
- Alembic migrations under `app/db/migrations`.

## Current capability labels
- **IMPLEMENTED**: endpoint/service/model exists and is wired.
- **BASELINE**: implemented with limited depth or calibration.
- **SYNTHETIC**: deterministic placeholder behavior.

## API surface (implemented)
Prefix: `/api/v1`

- Auth: `/auth/register`, `/auth/login`
- Health: `/health`, `/health/live`, `/health/ready`
- Users: `/users`, `/users/me`
- News: `/news/latest`, `/news/sources/reputation`, `/news/sources/reputation/refresh`
- Signals: `/signals/top`, `/signals/{signal_id}/recommendations`, `/signals/{signal_id}/explanation`
- Entities: `/entities`, `/entities/watchlist`, `/entities/provenance/refresh`
- On-chain: `/onchain/events`, `/onchain/state`
- Wallet: `/wallet/health`, `/wallet/profiles`, `/wallet/profiles/{wallet_profile_id}/health`, `/wallet/profiles/{wallet_profile_id}/health/reports`
- Fees: `/fees/recommendation`
- Privacy: `/privacy/assess`
- Treasury: `/treasury/requests`, `/treasury/requests/{request_id}/approve`, `/treasury/requests/{request_id}/reject`, `/treasury/requests/pending-approvals`
- Policy: `/policy/check`, `/policy/simulate`, `/policy/executions`, `/policy/executions/summary`, `/policy/catalog`, `/policy/catalog/compare`
- Citadel: `/citadel/overview`, `/citadel/assessment`, `/citadel/recalculate`, `/citadel/dependencies`, `/citadel/recovery`, `/citadel/simulations`, `/citadel/inheritance`, `/citadel/repair-plan`, `/citadel/policy-checks`
- Observability: `/observability/snapshot`
- Admin: `/admin/status`, `/admin/jobs`, `/admin/jobs/runs`, `/admin/jobs/recovery-check`, `/admin/jobs/retry`, `/admin/audit-logs`

## Runtime governance truth notes
- Runtime snapshot exposes `runtime_severity`, `degraded_mode`, and `operational_evidence` for operator triage.
- Degraded/fallback state is explicit and should be treated as lower-confidence runtime posture.
- Recovery SLO, drill posture, unresolved findings, and delivery health are surfaced for governance, not as hard production SLO attainment proof.
- Telegram and delivery flows remain **BASELINE** and environment-dependent.
- Citadel dependency graph and disaster simulations still include **SYNTHETIC** components.
- Migration reproducibility and schema parity checks are repository quality gates.

## Developer commands
```bash
make install-dev
make migrate
make run
make lint
```

Verification commands:
```bash
make test-contract
make migration-smoke
make docs-truthfulness
make ci
```

## Core documentation
- docs/API_CONTRACTS.md
- docs/DOMAIN_MODELS.md
- docs/STATUS.md
- docs/PRODUCTION_READINESS.md
- docs/OPERATIONS_RUNBOOK.md


## Release governance
- Release/RC checklist: `docs/PRODUCTION_READINESS.md`
- Operational rollback + incident notes: `docs/OPERATIONS_RUNBOOK.md`
- Release notes + exact verification command template: `docs/RELEASE_NOTES_TEMPLATE.md`
- Current truth-status and limitations: `docs/STATUS.md`


## Final readiness declaration
- Sovereignty-grade readiness (P7-06): **83%** (evidence-based; not an SLO claim).
- Current release decision: **PRE-RC / PRODUCTION-ORIENTED BETA**.
- Residual risks and next-release tasks are tracked in `docs/STATUS.md`.


## Documentation lock
- Documentation is locked to current implementation scope for RC (P7-03).
- Release sign-off must include residual-risk acknowledgement from `docs/STATUS.md` and checklist evidence from `docs/PRODUCTION_READINESS.md`.


## Release candidate metadata
- Candidate label and release-note structure are prepared in `docs/RELEASE_NOTES_TEMPLATE.md` (metadata-only; no tag implied).

- Next promotion requires closure evidence for protocol/Citadel realism and target-environment operational verification.


## Mining Sovereignty status
- **PLANNED / FOUNDATION SPEC**: Mining Sovereignty artifacts in this repository are planning/specification scaffolding only in M0.
- **NOT IMPLEMENTED**: production mining endpoints (`/api/v1/mining/pools`, `/pools/{pool_id}`, `/stratum-v2/adoption`, `/sovereignty-score`, `/censorship-risk`, `/template-control`, `/signals`) are contract drafts and are not runtime-implemented.
- Next block: **M1** (provider abstractions + read-only scoring/API path, still advisory and evidence-labeled).
