# Bitcoin Bastion Reflex Frontend

## Overview

The Reflex frontend is now the sole user interface for Bitcoin Bastion. As of 2026-06-29 the legacy Next.js codebase and related CI/compose resources have been removed. This repository directory (`reflex_frontend/`) contains a Python-first UI built with Reflex that interacts with the FastAPI backend.

Reflex remains under active development. While it has reached route/API parity for some public features, it does not yet claim full Market, Trace, Console, or production readiness. See `docs/ROUTE_API_PARITY.md` for the current parity status.

## Installation

Use Python 3.12 or newer and [uv](https://github.com/astral-sh/uv):

```bash
cd reflex_frontend
uv sync
```

## Running locally

Start the Reflex dev server with:

```bash
cd reflex_frontend
uv run reflex run --frontend-port 3001 --backend-port 8001
```

This will run the Reflex client on port `3001` and the Reflex backend on port `8001`. The FastAPI API should be accessible at `http://localhost:8000` by default. You can override these values via environment variables as described below.

## Environment variables

Reflex reads its configuration from `.env` or the environment. Copy `.env.example` to `.env` for local overrides.

```env
BB_API_BASE_URL=http://localhost:8000
BB_PUBLIC_SITE_MODE=true
BB_ENABLE_TRACE=true
BB_ENABLE_MARKET=true
BB_ENABLE_TIME_MACHINE=true
BB_ENABLE_SOVEREIGN_GRID=true
BB_ENABLE_CONSOLE=true
BB_REQUEST_TIMEOUT_SECONDS=5
BB_DEFAULT_LANGUAGE=en
```

Do not commit secrets. Reflex remains strictly no-custody and advisory-only.

## Ports

The default ports used in development:

- `3001`: Reflex frontend.
- `8001`: Reflex backend for API proxying.
- `8000`: FastAPI backend.

## Current capabilities

Reflex currently provides:

- The root public page `/` and initial static pages like `/platform`, `/developers`, `/operations`, `/manifesto`, `/evidence`, `/status`, `/roadmap`, `/security`, `/docs`.
- Early Trace Lite routes for `/check` and `/trace` that accept Bitcoin addresses only and display advisory-only results.
- Dynamic Trace routes `/trace/[report_id]` and `/trace/[report_id]/proof-packet` that call the FastAPI Trace endpoints.
- An early Bastion Console shell at `/console` with placeholder modules for Trace, Evidence, Provider Health, Policy, and Audit.
- A reusable API client layer with safe JSON envelope unwrapping, redacted logging, and no-custody semantics.
- A design system foundation with themes, layout primitives, safety components, and forbidden wording rules.

## Not yet implemented

The Reflex frontend does **not** yet include:

- Full Trace parity for all provider features.
- Market detail pages (the FastAPI/Jinja Market dashboard remains the authority for those routes).
- Console workflows beyond placeholder pages.
- Custody, signing, seed phrase handling, or private key handling.
- Full production readiness (load testing, WAF/CDN posture, accessibility audits, etc.).

## Safety rules

Bitcoin Bastion remains no-custody and advisory-only. Reflex must **never** request, store, transmit, derive, or display wallet secrets such as seed phrases, private keys, wallet files, or signing material. Backend APIs are the sole source of truth for data and domain behavior.

## Docker and Compose

You can build and run the Reflex frontend with Docker:

```bash
docker build -t bitcoin-bastion-reflex-frontend:local ./reflex_frontend
docker run --rm -p 3001:3001 -p 8001:8001 \
  -e BB_API_BASE_URL=http://host.docker.internal:8000 \
  bitcoin-bastion-reflex-frontend:local
```

To run Reflex in a compose stack with other services, use the provided compose files:

```bash
# just Reflex frontend and backend proxy
docker compose -f ../deploy/compose/reflex-frontend.compose.yaml up --build

# full Reflex stack plus backend dependencies
docker compose -f ../deploy/compose/full-reflex.compose.yaml up --build
```

`BB_API_BASE_URL` should point to the FastAPI backend. In container-to-container compose mode it is `http://api:8000`; in standalone local Docker runs it usually points to `http://host.docker.internal:8000`.

## CI expectations

The Reflex-specific CI workflow ensures that linting, typing, tests, export, and Docker build all succeed, and that safety/route parity checks remain enforced. Use `make reflex-ci`, `make frontend-safety-check`, `make frontend-route-parity`, and `make reflex-docker-build` locally to reproduce the CI steps.

CI passing does not itself declare Reflex production-ready; further evaluation and evidence are required.

## Removal of the old frontend

As of 2026-06-29 the legacy Next.js frontend has been deleted from the repository. The old `frontend/` directory, Next.js-specific CI workflow, and parallel compose configurations have been removed. To restore the legacy frontend for testing, check out the relevant commit from Git history or consult `docs/OLD_FRONTEND_REMOVAL_REPORT.md`. Reflex is now the only repository-native frontend; rollback requires retrieving the old code from the Git history.
