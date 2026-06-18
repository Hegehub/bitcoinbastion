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

## Navigation Foundation

Prompt 4 adds a centralized Reflex navigation registry plus public header, footer, mobile navigation, console sidebar, and command palette preview components.

- Canonical public navigation: Platform, Trace, Evidence, Status, Developers, Operations, Docs, Security, Roadmap.
- Trace is first-class in header, mobile navigation, footer, and command palette metadata.
- Console navigation items are rendered as preview or coming-soon shells until feature routes are implemented.
- Dynamic Trace Report and Proof Packet command actions require input; the shell does not guess report IDs.
- `/products` and `/self-host` are not canonical Reflex navigation targets; use `/platform` and `/operations` instead.
- Navigation metadata carries advisory and no-custody safety notes for Trace, Evidence, and policy-related surfaces.

This navigation foundation does not create business-page parity or production cutover readiness.

## API Client Layer

The Reflex API client layer is implemented under `bastion_ui/services/` and uses `bastion_ui.config.Settings` for environment-backed configuration.

- Backend base URL: `BB_API_BASE_URL`, defaulting to `http://localhost:8000` with trailing slashes stripped.
- Timeout: `BB_REQUEST_TIMEOUT_SECONDS`, defaulting to `5` seconds and validated as positive.
- Response envelopes: dictionaries with a `data` key return `data`; non-envelope JSON is returned unchanged; 204 responses return `None`.
- Error handling: HTTP, timeout, connection, and unreadable-response failures are normalized into safe frontend exceptions.
- No-custody logging: request bodies are not logged by default, and safe logging utilities redact wallet-secret-like material, authorization headers, API keys, webhook secrets, bearer tokens, and mnemonic-like strings.
- Tests: run `python -m pytest -q reflex_frontend/tests` from the repository root or `uv run pytest` from `reflex_frontend`.

This API layer does not migrate pages, fabricate backend results, or claim frontend parity.

## Public Static Routes

Prompt 6 registers the parallel Reflex public informational routes:

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

These routes use the shared public layout, header, footer, design-system components, safety copy, and conservative fallback states. Trace Lite (`/check`, `/trace`) and dynamic Trace report shells are now present; Market dashboards and Console modules remain deferred to later prompts.

Run locally from `reflex_frontend/` with `uv run reflex run --frontend-port 3001 --backend-port 8001` after installing dependencies with `uv sync`.

## Trace Lite Public Flow

Prompt 7 adds the first public Trace Lite flow in Reflex:

- `/check` for focused public Bitcoin address checks.
- `/trace` for the public Trace landing page and the same lightweight address-check flow.

The flow uses `/api/v1/trace/lite/{address}` through the shared API client. It accepts plausible public Bitcoin addresses beginning with `bc1`, `1`, or `3` and rejects sensitive wallet material before making an API request.

Trace remains advisory-only. It is not legal verification, not Bitcoin consensus proof, does not custody funds, and does not sign transactions. Detailed report pages and Proof Packet views are conservative shells until backend DTO alignment is complete.

## Trace Report Dynamic Routes

Prompt 8 adds dynamic Reflex route registrations for `/trace/[report_id]` and `/trace/[report_id]/proof-packet`.

- The Trace report page uses reusable panel components for overview, confidence, evidence, origin, privacy, source disagreement, UTXO hygiene, counterparty, and policy facts.
- Trace report state loads panels independently so partial backend failures remain visible instead of being hidden.
- Report identifiers are validated before API loading and suspicious path/script/scheme values are rejected.
- Proof packet rendering is conservative: if the backend endpoint is unavailable, the UI says the packet is unavailable and does not fake hashes or packet metadata.
- These routes remain advisory-only and do not implement custody, signing, legal verification, or Bitcoin consensus proof.
