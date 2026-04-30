# API Contracts

## Base conventions
- API prefix: `/api/v1`
- Most business endpoints return: `ResponseEnvelope[T]`
- List endpoints use pagination payload: `{"items": [...], "total": n, "limit": n, "offset": n}`
- Error envelope shape: `{"success": false, "error": {"code": "...", "message": "...", "request_id": "..."}}`

## Envelope exceptions (implemented)
These routes currently return direct models instead of `ResponseEnvelope`:
- `GET /api/v1/health` → `HealthOut`
- `GET /api/v1/health/live` → `HealthOut`
- `GET /api/v1/health/ready` → `HealthOut`
- `POST /api/v1/auth/register` → `UserOut`
- `POST /api/v1/auth/login` → `TokenResponse`

## Health & observability
- `GET /api/v1/health`
- `GET /api/v1/health/live`
- `GET /api/v1/health/ready`
- `GET /api/v1/observability/snapshot`
- `GET /metrics`

## Auth & users
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `GET /api/v1/users`
- `GET /api/v1/users/me`

## News & reputation
- `GET /api/v1/news/latest`
- `POST /api/v1/news/sources/reputation/refresh`
- `GET /api/v1/news/sources/reputation`

## Signals, entities, on-chain
- `GET /api/v1/signals/top` (supports `horizon=short|medium|long`)
- `GET /api/v1/signals/{signal_id}/explanation`
- `GET /api/v1/signals/{signal_id}/recommendations` (includes `evidence_refs`, `evidence_paths`, `policy_refs`)
- `GET /api/v1/entities` (includes `source_ref_count`, `provenance_score`, `provenance_tier`)
- `GET /api/v1/entities/watchlist`
- `POST /api/v1/entities/provenance/refresh` (admin; drift-aware confidence refresh + per-entity delta summary)
- `GET /api/v1/onchain/events`
- `GET /api/v1/onchain/state`

## Wallet, fees, privacy, treasury
- `POST /api/v1/wallet/health`
- `POST /api/v1/wallet/profiles/{wallet_profile_id}/health`
- `GET /api/v1/wallet/profiles/{wallet_profile_id}/health/reports`
- `GET /api/v1/wallet/profiles`
- `POST /api/v1/fees/recommendation`
- `POST /api/v1/privacy/assess`
- `POST /api/v1/treasury/requests`
- `POST /api/v1/treasury/requests/{request_id}/approve` (admin)
- `POST /api/v1/treasury/requests/{request_id}/reject` (admin)
- `GET /api/v1/treasury/requests/pending-approvals` (admin)
- `GET /api/v1/treasury/requests`

## Policy & education
- `POST /api/v1/policy/check`
- `POST /api/v1/policy/simulate` (admin, returns risk classification + governance actions)
- `GET /api/v1/policy/executions`
- `GET /api/v1/policy/executions/summary` (admin)
- `POST /api/v1/policy/catalog` (admin; high-risk tightening requires `change_justification`)
- `POST /api/v1/policy/catalog/compare` (admin; threshold/rule diff between two policy profiles)
- `GET /api/v1/policy/catalog`
- `GET /api/v1/education/snippets`

## Citadel
- `GET /api/v1/citadel/overview`
- `GET /api/v1/citadel/assessment`
- `POST /api/v1/citadel/recalculate`
- `GET /api/v1/citadel/dependencies`
- `GET /api/v1/citadel/recovery`
- `POST /api/v1/citadel/simulations`
- `GET /api/v1/citadel/simulations`
- `GET /api/v1/citadel/inheritance`
- `GET /api/v1/citadel/repair-plan`
- `GET /api/v1/citadel/policy-checks`

## Admin operations
- `GET /api/v1/admin/status`
- `GET /api/v1/admin/jobs`
- `GET /api/v1/admin/jobs/runs`
- `GET /api/v1/admin/audit-logs`
- `GET /api/v1/admin/jobs/recovery-check` (returns `severity=ok|warning|critical`)
- `POST /api/v1/admin/jobs/retry`

## Guards and operational behavior
- Auth-protected routes use JWT bearer dependencies.
- Admin routes require elevated role checks.
- Rate limit violations return HTTP `429` with `code=rate_limited`.
- Request ID middleware propagates traceability for all error envelopes.
