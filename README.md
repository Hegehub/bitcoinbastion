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

## Runtime truth notes
- Telegram and delivery flows are **BASELINE** (environment-dependent runtime behavior).
- Citadel dependency graph and disaster simulation outputs include **SYNTHETIC** components.
- Migration reproducibility and schema parity checks are part of repository quality gates.
- Protocol-aware outputs include explicit source-quality labels; fallback/synthetic domains should be treated as lower-confidence operational signals.

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
```

## Core documentation
- docs/API_CONTRACTS.md
- docs/DOMAIN_MODELS.md
- docs/STATUS.md
- docs/PRODUCTION_READINESS.md
