# API gateway

Owns external ingress, request routing, edge rate limits, request size limits, CORS policy and public API exposure boundaries.

Current canonical paths:

- `app/api/middleware.py`
- ingress/API deployment configuration under `deploy/`

Migration rule: gateway policy must be explicit, testable and aligned with backend router prefixes.
