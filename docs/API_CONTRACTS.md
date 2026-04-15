# API Contracts

## Base conventions
- API prefix: `/api/v1`
- Most endpoints return: `ResponseEnvelope[T]`
- List endpoints use pagination payload: `{"items": [...], "total": n, "limit": n, "offset": n}`
- Error envelope shape: `{"success": false, "error": {"code": "...", "message": "...", "request_id": "..."}}`

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
- `GET /api/v1/signals/{signal_id}/recommendations`
- `GET /api/v1/entities`
- `GET /api/v1/onchain/events`

## Wallet, fees, privacy, treasury
- `POST /api/v1/wallet/health`
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
- `GET /api/v1/policy/executions`
- `POST /api/v1/policy/catalog` (admin)
- `GET /api/v1/policy/catalog`
- `GET /api/v1/education/snippets`

## Admin operations
- `GET /api/v1/admin/status`
- `GET /api/v1/admin/jobs`
- `GET /api/v1/admin/audit-logs`
- `GET /api/v1/admin/jobs/runs`
- `POST /api/v1/admin/jobs/retry`

## Guards and operational behavior
- Auth-protected routes use JWT bearer dependencies.
- Admin routes require elevated role checks.
- Rate limit violations return HTTP `429` with `code=rate_limited`.
- Request ID middleware propagates traceability for all error envelopes.
