# Bitcoin Bastion Experimental Reflex Frontend

This directory contains an experimental Python-first Reflex frontend shell for Bitcoin Bastion. It is a parallel public UI layer for future implementation work and is not the production primary frontend.

## Current ownership boundaries

- Reflex does not replace Next.js yet. It runs parallel to Next.js.
- The existing `frontend/` Next.js app remains available until route and API parity are proven with evidence.
- Reflex does not replace the FastAPI backend.
- FastAPI remains the source of truth for business logic, domain logic, data validation, calculations, and API responses.
- `/market` remains owned by the existing FastAPI/Jinja Market Time Machine dashboard for now.
- This scaffold does not claim route parity, API parity, Trace migration, Console implementation, or production readiness.

## Ports

- Existing Next.js legacy frontend: `3000`
- Experimental Reflex frontend: `3001`
- Experimental Reflex backend: `8001`
- Existing FastAPI backend: `8000`

## Setup and run

Use `uv` with Python 3.12 or newer:

```bash
cd reflex_frontend
uv sync
uv run reflex run
```

## Test commands

```bash
cd reflex_frontend
uv run ruff check .
uv run mypy bastion_ui
uv run pytest
uv run reflex export
```

## Current implemented routes

- `/`
- `/platform`
- `/developers`
- `/operations`
- `/manifesto`
- `/evidence`
- `/status`
- `/roadmap`
- `/security`
- `/docs`

Trace (`/trace`, `/check`) and Console (`/console`, `/console/time-machine`, `/console/sovereign-grid`) links are visible for navigation continuity, but Prompt 26 will add their implementations.

## Safety constraints

Bitcoin Bastion remains Bitcoin-first, no-custody, advisory-only, and operator-controlled. This Reflex shell must not request, store, transmit, derive, or display seed phrases, private keys, wallet files, signing material, or custody workflows.

Required safety copy for public UI surfaces includes:

- Advisory-only.
- Not legal verification.
- Not Bitcoin consensus proof.
- No custody.
- Public Bitcoin addresses only.
- Never enter seed phrases, private keys, wallet files or signing material.

## Development scope

The current Reflex layer provides the public design system, shared layout, navigation, command palette, safety components, i18n baseline, and public pages. Future prompts will add Trace, Console surfaces, CI hardening, and the wow layer. Until parity is proven, this remains an experimental shell that can run in parallel with the existing frontend stack.

## Prompt 26 Trace and Console layer

Implemented experimental routes:

- `/check`
- `/trace`
- `/trace/[report_id]`
- `/trace/[report_id]/proof-packet`
- `/console`
- `/console/trace`
- `/console/evidence`
- `/console/provider-health`

Trace uses the FastAPI backend as source of truth through the Reflex API client. Public Bitcoin address validation rejects seed phrases, private keys, wallet files, keystores, extended private keys, and signing material before backend calls.

Proof Packet views are frontend-ready if public backend proof-packet data is unavailable. Missing proof data must be shown as unavailable and must not be treated as certified evidence.

Docker Compose service snippet for operators who want to run Reflex in parallel:

```yaml
reflex-frontend:
  build:
    context: ./reflex_frontend
  environment:
    BB_API_BASE_URL: http://api:8000
    BB_PUBLIC_SITE_MODE: "true"
    BB_ENABLE_TRACE: "true"
    BB_ENABLE_CONSOLE: "true"
    BB_REQUEST_TIMEOUT_SECONDS: "5"
  ports:
    - "3001:3001"
    - "8001:8001"
  depends_on:
    - api
```

## Prompt 27 Advanced Console modules

Advanced Console modules are implemented as preview/operator visibility pages. They are not production control-plane mutation tools, do not replace `/market`, do not replace backend authority, and do not perform custody, signing, transaction creation, transaction broadcasting, or treasury execution.

Advanced Console routes:

- `/console/market-intelligence`
- `/console/time-machine`
- `/console/sovereign-grid`
- `/console/policy`
- `/console/audit`
- `/console/deployment`
- `/console/api-explorer`

Every module is read-only, advisory, evidence-oriented, and operator-review focused. Degraded, fallback, stale, and unavailable states are intentionally visible.
