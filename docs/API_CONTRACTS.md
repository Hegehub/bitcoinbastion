# API Contracts

## Base conventions
- API prefix: `/api/v1`
- Most business endpoints return `ResponseEnvelope[T]`
- List endpoints use `PaginatedData`
- Error envelope shape: `{"success": false, "error": {"code": "...", "message": "...", "request_id": "..."}}`

## Envelope exceptions (implemented)
- `GET /api/v1/health`
- `GET /api/v1/health/live`
- `GET /api/v1/health/ready`
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`

## Implemented route inventory

### Health and observability
- `GET /api/v1/health`
- `GET /api/v1/health/live`
- `GET /api/v1/health/ready`
- `GET /api/v1/observability/snapshot`
- `GET /metrics`

### Auth and users
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `GET /api/v1/users`
- `GET /api/v1/users/me`

### News
- `GET /api/v1/news/latest`
- `POST /api/v1/news/sources/reputation/refresh`
- `GET /api/v1/news/sources/reputation`

### Signals, entities, on-chain
- `GET /api/v1/signals/top`
- `GET /api/v1/signals/{signal_id}/recommendations`
- `GET /api/v1/signals/{signal_id}/explanation`
- `GET /api/v1/entities`
- `GET /api/v1/entities/watchlist`
- `POST /api/v1/entities/provenance/refresh`
- `GET /api/v1/onchain/events`
- `GET /api/v1/onchain/state`

### Wallet, fees, privacy, treasury
- `POST /api/v1/wallet/health`
- `POST /api/v1/wallet/profiles/{wallet_profile_id}/health`
- `GET /api/v1/wallet/profiles/{wallet_profile_id}/health/reports`
- `GET /api/v1/wallet/profiles`
- `POST /api/v1/fees/recommendation`
- `POST /api/v1/privacy/assess`
- `POST /api/v1/treasury/requests`
- `POST /api/v1/treasury/requests/{request_id}/approve`
- `POST /api/v1/treasury/requests/{request_id}/reject`
- `GET /api/v1/treasury/requests/pending-approvals`
- `GET /api/v1/treasury/requests`

### Policy and education
- `POST /api/v1/policy/check`
- `POST /api/v1/policy/simulate`
- `GET /api/v1/policy/executions`
- `GET /api/v1/policy/executions/summary`
- `POST /api/v1/policy/catalog`
- `POST /api/v1/policy/catalog/compare`
- `GET /api/v1/policy/catalog`
- `GET /api/v1/education/snippets`

### Citadel
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

### Admin
- `GET /api/v1/admin/status`
- `GET /api/v1/admin/jobs`
- `GET /api/v1/admin/jobs/runs`
- `GET /api/v1/admin/audit-logs`
- `GET /api/v1/admin/jobs/recovery-check`
- `POST /api/v1/admin/jobs/retry`

## Observability snapshot contract notes (implemented)
`GET /api/v1/observability/snapshot` includes:
- `runtime_severity`: deterministic severity score/level, escalation conditions, operator guidance.
- `degraded_mode`: explicit degraded-runtime marker, degraded reasons, component states, confidence penalty.
- `operational_evidence`: compact operational audit packet with runtime state, degraded dependencies, provider quality, unresolved findings, delivery health, drill status, and recovery SLO status.

These fields are operational governance aids and not guarantees of external SLO attainment.

## Protocol source-quality fields (implemented)
- `GET /api/v1/onchain/state` includes source-quality metadata in `freshness` and `explainability` (including fallback/mock semantics when applicable).
- Citadel explainability includes `input_quality` and `protocol_input_quality` domains to expose protocol data maturity and fallback/synthetic limitations.
- Mempool/UTXO service-driven outputs include source-quality/freshness limitations in explainability fields; these are advisory and conservative.
