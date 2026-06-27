# Frontend Runtime Modes

## 1. `api-only` mode

Runs the FastAPI backend without a web frontend. Best for SDK/API consumers, automation tests, or operators exposing only API endpoints.

- Services: FastAPI, PostgreSQL, Redis, worker, beat as needed.
- Ports: `8000` for FastAPI.
- Limitations: no browser frontend.
- Rollback path: enable `nextjs` or `parallel` mode.
- Production suitability: possible for API-only deployments with normal backend evidence.

## 2. `nextjs` mode

Runs FastAPI plus the legacy Next.js frontend.

- Services: backend services plus `frontend` when configured.
- Ports: `8000` and `3000`.
- Limitations: Reflex migration surfaces are not active.
- Rollback path: this is the current rollback path.
- Production suitability: current stable/legacy frontend mode.

## 3. `reflex` mode

Runs FastAPI plus the Reflex frontend.

- Services: backend services plus `reflex-frontend`.
- Ports: `8000`, `3001`, and `8001`.
- Limitations: not primary until Prompt 21/22; FastAPI/Jinja Market remains active until parity decisions.
- Rollback path: switch back to `nextjs` or `parallel` mode.
- Production suitability: migration target only until cutover evidence is complete.

## 4. `parallel` mode

Runs FastAPI, legacy Next.js, and Reflex together for route/API/visual comparison.

- Services: backend services, `frontend`, and `reflex-frontend`.
- Ports: `8000`, `3000`, `3001`, and `8001`.
- Limitations: more local resources; not a final production topology by itself.
- Rollback path: stop Reflex and continue with Next.js.
- Production suitability: recommended migration validation mode, not final cutover.

## 5. Route ownership during migration

- Next.js: legacy active.
- Reflex: parallel migration target.
- FastAPI/Jinja Market: active until market parity and cutover decisions are complete.
- FastAPI backend: source of backend data and domain behavior.

## 6. Cutover not complete until Prompt 21/22

This repository now supports Reflex deployment, but route ownership does not change in Prompt 19/22. Do not treat Reflex as the primary frontend until the later cutover prompt and its evidence gates are complete.

## 7. Recommended mode during migration

Use `parallel` mode for migration comparison because it keeps the legacy frontend available while Reflex is exercised on ports `3001` and `8001`.

## 8. Production warning

Do not claim production cutover or production readiness from frontend mode metadata alone. Production claims require health checks, observability, backups, recovery drills, secrets handling validation, route parity, and rollback evidence.

## 9. Rollback path

Return to `nextjs` mode or the existing root `docker-compose.yml`. Do not delete `frontend/`, FastAPI/Jinja Market routes, or legacy deployment support until final cutover is explicitly completed.
