# Reflex Deployment

## 1. Purpose

This guide explains how to deploy the Bitcoin Bastion Reflex frontend alongside the backend. Reflex is the only repository‑native web interface. The legacy Next.js frontend and associated compose files have been removed from the working tree.

## 2. Current status

- **Reflex status:** migration‑primary and default UI layer.
- **FastAPI/Jinja Market status:** continues to serve the Market dashboard and certain drill‑down pages until those surfaces are fully reimplemented in Reflex.
- **FastAPI backend status:** source of data and domain behavior.

## 3. Ports

| Service | Port |
| --- | ---: |
| FastAPI backend | `8000` |
| Reflex frontend | `3001` |
| Reflex backend/control | `8001` |

## 4. Environment variables

Reflex deployment files set only non‑secret frontend configuration:

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

Do not put seed phrases, private keys, wallet files, signing material, API secrets or production credentials in compose files.

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

The image uses Python 3.12 slim, `uv sync --frozen --no-dev`, the Reflex project lockfile and the Reflex‑supported `reflex run --env prod` command.

## 6. Backend + Reflex compose mode

Use the full Reflex compose file for backend dependencies plus Reflex:

```bash
docker compose -f deploy/compose/full-reflex.compose.yaml config
docker compose -f deploy/compose/full-reflex.compose.yaml up --build
```

This starts PostgreSQL, Redis, API, worker, beat and `reflex-frontend`. The Reflex service points `BB_API_BASE_URL` at `http://api:8000`.

## 7. Runtime profile frontend modes

Runtime profile metadata now includes frontend mode information. Only two frontend modes are available because the legacy Next.js frontend and parallel migration mode have been removed.

| Mode | Best for | Ports | Services | Limitations | Production suitability |
| --- | --- | --- | --- | --- | --- |
| `api-only` | SDK/API deployments and backend‑only tests | `8000` | FastAPI and backend dependencies | no browser frontend | Suitable for API‑only scenarios |
| `reflex` | Primary user interface | `8000`, `3001`, `8001` | FastAPI backend plus Reflex frontend | Market dashboard and drill‑down pages remain served by FastAPI/Jinja until full parity is achieved | Suitable when used with backend production evidence |

Runtime metadata fields include `frontend.mode`, `frontend.primary`, `reflex_enabled`, `cutover_ready` and `rollback_available`. With the legacy frontend removed, `frontend.primary` is now `reflex`, `reflex_enabled` is `true`, `cutover_ready` should be set once parity gates pass, and `rollback_available` is `false` because restoring the old frontend requires retrieving the deleted directory from version control.

## 8. Healthcheck notes

The Reflex Dockerfile and compose files use a simple HTTP check against `/` on port `3001`. Compose `depends_on` ordering does not prove full production readiness; production deployments still need real health/readiness, logs, metrics, backup, recovery and operator evidence.

## 9. Known limitations

- Market detail and drill‑down routes remain served by FastAPI/Jinja until Reflex achieves full parity. Operators should treat these pages as advisory only.
- Compose files use local‑development defaults for PostgreSQL passwords unless operators override them.
- Compose is not HA and does not certify production readiness.
- Full production readiness requires environment‑specific evidence, backup/restore evidence, monitoring validation and operator drills.

## 10. Rollback and legacy note

The old Next.js frontend and the parallel compose file have been removed. To return to the legacy user interface, maintainers would need to restore the `frontend/` directory and associated CI/workflow files from Git history or a tagged archive. This guide does not describe how to run the legacy frontend because it is no longer present in the working tree.
