# Reflex Deployment

## 1. Purpose

This guide explains how to run the Bitcoin Bastion Reflex frontend as an optional, parallel deployment surface. Reflex is not the primary frontend yet and does not replace the legacy Next.js frontend or the FastAPI/Jinja Market dashboard in this prompt.

## 2. Current migration status

- Next.js status: legacy active frontend.
- Reflex status: parallel migration target.
- FastAPI/Jinja Market status: active until market parity and cutover decisions are completed.
- FastAPI backend status: source of data and domain behavior.
- Cutover status: not complete until Prompt 21/22.

## 3. Ports

| Service | Port |
| --- | ---: |
| FastAPI backend | `8000` |
| Legacy Next.js frontend | `3000` |
| Reflex frontend | `3001` |
| Reflex backend/control | `8001` |

## 4. Environment variables

Reflex deployment files set only non-secret frontend configuration:

```env
BB_API_BASE_URL=http://api:8000
BB_PUBLIC_SITE_MODE=true
BB_ENABLE_TRACE=true
BB_ENABLE_TIME_MACHINE=true
BB_ENABLE_SOVEREIGN_GRID=true
BB_ENABLE_CONSOLE=true
BB_REQUEST_TIMEOUT_SECONDS=5
BB_DEFAULT_LANGUAGE=en
```

Do not put seed phrases, private keys, wallet files, signing material, API secrets, or production credentials in compose files.

## 5. Standalone Reflex container

Build the standalone image:

```bash
docker build -t bitcoin-bastion-reflex-frontend:local ./reflex_frontend
```

Run it against a backend reachable from the host:

```bash
docker run --rm -p 3001:3001 -p 8001:8001 \
  -e BB_API_BASE_URL=http://host.docker.internal:8000 \
  bitcoin-bastion-reflex-frontend:local
```

The image uses Python 3.12 slim, `uv sync --frozen --no-dev`, the Reflex project lockfile, and the Reflex-supported `reflex run --env prod` command.

## 6. Backend + Reflex compose mode

Use the full Reflex compose file for backend dependencies plus Reflex:

```bash
docker compose -f deploy/compose/full-reflex.compose.yaml config
docker compose -f deploy/compose/full-reflex.compose.yaml up --build
```

This starts PostgreSQL, Redis, API, worker, beat, and `reflex-frontend`. The Reflex service points `BB_API_BASE_URL` at `http://api:8000`.

## 7. Parallel Next.js + Reflex compose mode

Use the parallel compose file during migration comparison:

```bash
docker compose -f deploy/compose/full-parallel-frontends.compose.yaml config
docker compose -f deploy/compose/full-parallel-frontends.compose.yaml up --build
```

This starts backend services, the legacy Next.js frontend on `3000`, and Reflex on `3001`/`8001`. The Next.js service uses the existing `frontend/` workspace through a local bind mount because no legacy `frontend/Dockerfile` exists yet.

## 8. Runtime profile frontend modes

Runtime profile metadata now recognizes four frontend modes:

| Mode | Meaning | Production suitability |
| --- | --- | --- |
| `api-only` | FastAPI backend only. | API/SDK deployments only. |
| `nextjs` | Backend plus legacy Next.js. | Current stable frontend path. |
| `reflex` | Backend plus Reflex. | Migration target; not primary yet. |
| `parallel` | Backend plus Next.js and Reflex. | Recommended during migration comparison. |

## 9. Healthcheck notes

The Reflex Dockerfile and compose files use a simple HTTP check against `/` on port `3001`. Compose `depends_on` ordering does not prove full production readiness; production deployments still need real health/readiness, logs, metrics, backup, recovery, and operator evidence.

## 10. Known limitations

- Reflex is not the primary frontend yet.
- The parallel Next.js compose service is development/migration oriented because the legacy frontend does not currently provide a Dockerfile; it uses a local writable bind mount for the existing `frontend/` workspace and should not be treated as a hardened production mount.
- Compose files use local-development defaults for PostgreSQL passwords unless operators override them.
- Compose is not HA and does not certify production readiness.

## 11. Rollback path

Keep Next.js running or return to `docker-compose.yml` / `nextjs` mode. Reflex can be stopped independently without deleting `frontend/` or FastAPI/Jinja Market routes.

## 12. Why Next.js is not deleted yet

Next.js remains the rollback and comparison surface until Prompt 21/22 cutover gates pass. Reflex deployment support in this prompt proves optional runtime viability only; it does not transfer route ownership.
