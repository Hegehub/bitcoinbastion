# Backend

Owns FastAPI application composition, HTTP routing boundaries, domain service coordination and runtime integration.

Current canonical paths:

- `app/main.py`
- `app/api/`
- `app/services/`
- `app/core/`

Migration rule: do not move `app/` imports without a dedicated refactor that updates routers, tests and deployment entrypoints together.
