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

## Wow Layer

The Wow Layer is an evidence-oriented, sovereignty-first UI foundation for the experimental Reflex Console. It adds Trace Radar, Evidence Chain Viewer, Proof Packet Explorer, Time Machine Timeline, Sovereignty Score Panel, Node Pulse, Provider Trust Matrix, Human Confirmation Firewall, Trace Story Mode, Policy Engine Simulator, Risk Heatmap, Operator Audit Replay, Market Intelligence Wall, Historical Similarity Lens, Sovereign Grid Map, API Contract Explorer, Privacy Exposure Lens, Citadel Mode, and the No-Custody Safety Layer.

What it is not:

- It is not a replacement for Next.js.
- It is not a replacement for the FastAPI backend.
- It is not a replacement for the FastAPI/Jinja `/market` dashboard.
- It is not production-primary yet.
- It does not calculate backend risk, score, Trace verdicts, or market conclusions in the frontend.
- It does not perform custody, signing, transaction creation, transaction broadcasting, or risky action execution.

The backend remains the source of truth. Preview mode is explicit. Degraded, fallback, stale, unavailable, and unknown states are intentionally visible. Forbidden wording is not allowed in public operator surfaces.

Checklist:

- [x] Trace Radar
- [x] Evidence Chain Viewer
- [x] Proof Packet Explorer
- [x] Time Machine Timeline
- [x] Sovereignty Score Panel
- [x] Node Pulse
- [x] Provider Trust Matrix
- [x] Human Confirmation Firewall
- [x] Policy Engine Simulator
- [x] Risk Heatmap
- [x] Operator Audit Replay
- [x] Market Intelligence Wall
- [x] Historical Similarity Lens
- [x] Sovereign Grid Map
- [x] API Contract Explorer
- [x] Privacy Exposure Lens
- [x] Citadel Mode
- [x] No-Custody Safety Layer
