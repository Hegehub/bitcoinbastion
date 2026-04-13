# API Contracts

All list-style responses use envelope:
- `{"success": true, "data": {"items": [...], "total": n, "limit": n, "offset": n}}`

Main groups:
- `/api/v1/auth`
- `/api/v1/news`
- `/api/v1/signals`
- `/api/v1/onchain`
- `/api/v1/entities`
- `/api/v1/wallet`
- `/api/v1/fees`
- `/api/v1/treasury`
- `/api/v1/admin`
- `/api/v1/users`

Additional production endpoints:
- `/api/v1/wallet/profiles` (auth, paginated)
- `/api/v1/treasury/requests` GET/POST (auth, paginated for GET)
- `/api/v1/health/live` and `/api/v1/health/ready`
- `/api/v1/admin/jobs` (admin, Celery task visibility)
- `/api/v1/admin/jobs/runs` (admin, persisted job run history)
- `/api/v1/admin/jobs/retry` (admin, re-dispatch failed/stuck task by name)
- `/metrics` (Prometheus format)

Error envelope:
- `{"success": false, "error": {"code": "...", "message": "...", "request_id": "..."}}`
- Rate limit errors return HTTP 429 with `code=rate_limited`.
