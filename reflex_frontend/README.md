# Bitcoin Bastion Reflex Frontend

## 1. Purpose

This Reflex frontend is a parallel migration shell. It provides the isolated Python-first foundation for the controlled migration from the legacy-supported Next.js frontend to Reflex.

## 2. Current status

- Current status: parallel shell only.
- Current implemented Reflex route: `/`.
- It does not replace the existing Next.js frontend yet.
- It does not replace the FastAPI backend.
- It does not replace the FastAPI/Jinja Market dashboard.
- It does not claim route parity, API parity, Trace parity, Market parity, Console parity, or production readiness.

## 3. How to install

Use Python 3.12 or newer and `uv`:

```bash
cd reflex_frontend
uv sync
```

## 4. How to run locally

```bash
cd reflex_frontend
uv run reflex run --frontend-port 3001 --backend-port 8001
```

## 5. Environment variables

Copy `.env.example` to `.env` for local overrides if needed.

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

No secrets should be committed.

## 6. Ports

- Existing Next.js frontend: `3000`.
- Parallel Reflex frontend: `3001`.
- Parallel Reflex backend: `8001`.
- Existing FastAPI backend: `8000`.

## 7. What this frontend currently does

- Defines the Reflex project configuration.
- Provides a minimal root page at `/`.
- Loads settings from `BB_` environment variables.
- Provides a minimal async API client foundation with `ResponseEnvelope.data` unwrapping.
- Provides an early sensitive wallet-material detector.
- Provides scaffold tests that do not require a running backend.

## 8. What this frontend does not do yet

- It does not migrate Trace routes yet.
- It does not migrate Market routes yet.
- It does not create Console routes yet.
- It does not implement full navigation parity yet.
- It does not replace production frontend behavior.
- It does not implement custody, signing, seed phrase handling, or private key handling.

## 9. Safety rules

Bitcoin Bastion remains no-custody and advisory-only.

Never enter seed phrases, private keys, wallet files, or signing material.

This shell must not request, store, transmit, derive, or display wallet secrets. Backend APIs remain the source of truth for data and domain behavior.

## 10. Migration notes

Next.js remains the active legacy-supported frontend until explicit cutover gates are satisfied in later prompts. The FastAPI/Jinja Market dashboard remains unchanged. Future prompts will add design system foundations, route registration, service-specific API clients, Trace parity, Market parity, Console parity, CI, and cutover evidence.

## Design System Foundation

Prompt 3 adds the reusable foundation for later Reflex pages:

- theme tokens for color, spacing, typography, risk bands, evidence states, and data states;
- layout primitives for public shells, console shells, containers, sections, grids, and stacks;
- safety components for advisory, no-custody, limitations, and forbidden-input notices;
- degraded, stale, loading, and sanitized error state components;
- `/design-system` preview route for development verification;
- safety constraints that prohibit wallet-secret collection, signing workflows, auto-execution UI, legal verdict language, and financial advice language;
- forbidden wording rules that prevent stigmatizing or certainty-implying address/payment phrases in user-facing modules.

The design-system route is a development preview only. It is not production parity, and it is not a cutover route.

## API Client Layer

Prompt 5 adds the reusable API client layer for future Reflex routes. The layer keeps FastAPI as the source of truth and does not duplicate backend scoring, Trace, Evidence, Market, Console, or Policy logic.

- Configuration is loaded from `BB_` environment variables in `bastion_ui.config.AppConfig`.
- `BB_API_BASE_URL` points to the FastAPI backend and strips trailing slashes.
- `BB_REQUEST_TIMEOUT_SECONDS` controls the HTTP timeout and must be positive.
- `BastionApiClient` supports `GET`, `POST`, `PATCH`, and `DELETE` through `httpx.AsyncClient`.
- Response envelopes are unwrapped by returning `data` when the backend sends `{ "data": ... }`.
- If an envelope contains a non-null `error`, the client raises a normalized safe API error.
- Public, Trace, Evidence, Status, Market, and Console client modules only build calls to backend endpoints; they do not fabricate data.
- Safe logging utilities redact wallet-secret-like text, authorization headers, API keys, webhook secrets, bearer/session tokens, and mnemonic-like word sequences.

Run API client tests from the repository root:

```bash
python -m pytest -q reflex_frontend/tests
```

Run the Reflex package checks:

```bash
cd reflex_frontend
uv run ruff check .
uv run mypy bastion_ui
uv run pytest
```

This API client layer is not route parity, frontend parity, or production cutover readiness.

## Public Static Routes

Prompt 6 registers the initial Reflex-owned public informational routes during the parallel migration phase:

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

These pages use the shared public layout, header, footer, safety copy, and conservative fallback states. They do not implement `/check`, full Trace, Proof Packet, Market dashboard, or Console workflows yet. Next.js remains available until documented cutover gates pass.

## Trace Lite Public Flow

Prompt 7 adds two public Trace Lite entrypoints:

- `/check`
- `/trace`

Both routes accept public Bitcoin addresses only and use `/api/v1/trace/lite/{address}` through the shared Reflex API client. The flow rejects obvious wallet-secret material before API submission and displays advisory-only/no-custody limitations. Full report routes and Proof Packet routes remain future migration prompts.

## Trace Report Dynamic Routes

Prompt 8 adds Reflex dynamic Trace routes for `/trace/[report_id]` and `/trace/[report_id]/proof-packet`.

The report UI is advisory-only and panel based. It calls the FastAPI Trace endpoints through the shared API client and keeps missing, partial, degraded, or stale panel states visible. The Proof Packet route does not fabricate packet contents or hashes when the backend endpoint is unavailable or access-limited.

These routes do not complete Trace parity. Full Proof Packet/Evidence parity, export behavior, and deeper Evidence UI remain later migration work.

## Proof Packet and Evidence UI

Prompt 9 adds the Evidence and Proof Packet UI layer for the Reflex migration. The `/evidence` route explains Evidence limitations and degraded/provider-disputed states, while `/trace/[report_id]/proof-packet` shows Proof Packet status and backend-provided evidence only when available.

The UI does not fabricate packet data, hashes, source lists, or legal conclusions. It remains advisory-only, no-custody, and limited by backend endpoint availability and provider quality.
