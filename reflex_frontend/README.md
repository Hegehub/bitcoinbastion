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

## Bastion Console Shell

The Reflex app includes a foundational Bastion Console shell at `/console` with safe placeholder routes for `/console/trace`, `/console/evidence`, `/console/provider-health`, `/console/policy`, and `/console/audit`.

The console shell is advisory/operator-review focused. Module internals are implemented progressively in later prompts; the shell does not execute risky actions, sign transactions, request wallet secrets, or claim production readiness. Unknown, degraded, stale, and fallback states are shown explicitly instead of being hardcoded as healthy.

## Wow Layer

The wow layer provides operator-oriented visualizations for Trace, Evidence, Provider Health, Market Intelligence, Policy, Audit, and runtime posture. It does not create legal verdicts, financial advice, custody flows, or Bitcoin consensus proofs.

## Accessibility, i18n, and Safety Copy

Accessibility baseline helpers, English/Russian i18n scaffolding, and centralized safety copy are documented in `docs/ACCESSIBILITY.md`, `docs/I18N.md`, and `docs/SAFETY_COPY.md`. Manual accessibility audit is still recommended before production cutover.

## Testing

Run the Reflex migration test suite from this directory:

```bash
uv sync
uv run ruff check .
uv run mypy bastion_ui
uv run pytest
uv run reflex export
```

The broader repository suite can be run from the repository root with `python -m pytest -q`, but root-level failures outside `reflex_frontend/` are tracked as migration blockers until the baseline async/test-environment gaps are resolved.

## Docker and Compose

Build the standalone Reflex image from the repository root:

```bash
docker build -t bitcoin-bastion-reflex-frontend:local ./reflex_frontend
```

Run Reflex as a standalone container against an externally reachable FastAPI backend:

```bash
docker run --rm -p 3001:3001 -p 8001:8001 \
  -e BB_API_BASE_URL=http://host.docker.internal:8000 \
  bitcoin-bastion-reflex-frontend:local
```

Run only the Reflex frontend service with compose:

```bash
docker compose -f ../deploy/compose/reflex-frontend.compose.yaml up --build
```

Run backend dependencies plus Reflex:

```bash
docker compose -f ../deploy/compose/full-reflex.compose.yaml up --build
```

Run legacy Next.js and Reflex in parallel for migration comparison:

```bash
docker compose -f ../deploy/compose/full-parallel-frontends.compose.yaml up --build
```

`BB_API_BASE_URL` controls the FastAPI backend target. In container-to-container compose mode it is `http://api:8000`; in standalone local Docker runs it usually points to `http://host.docker.internal:8000` or another operator-provided API URL.

Known limitations: Reflex remains a parallel migration target, Next.js is still the rollback surface, FastAPI/Jinja Market routes are not removed, and production cutover is not complete until later migration gates pass. Do not commit secrets or mount wallet files/signing material into the Reflex container.

## CI expectations

The Reflex-specific CI workflow runs on Reflex, workflow, and Reflex CI documentation changes. It checks:

1. `uv sync`
2. `uv run ruff check .`
3. `uv run mypy bastion_ui`
4. `uv run pytest`
5. `uv run reflex export`
6. `docker build -f reflex_frontend/Dockerfile -t bitcoin-bastion-reflex-frontend:test reflex_frontend`
7. focused safety/no-custody/forbidden-wording tests
8. focused route/navigation/command-palette parity tests

Local equivalent:

```bash
make reflex-ci
make frontend-safety-check
make frontend-route-parity
make reflex-docker-build
```

CI passing does not make Reflex the primary frontend. Next.js remains the rollback surface and the primary switch is controlled by the Prompt 21/22 cutover gates.

## Final migration audit status

Prompt 22/22 confirms Reflex as the preferred primary migration frontend, but not a blanket production-ready replacement. Next.js remains in `frontend/` as rollback, FastAPI/Jinja Market detail routes remain delegated where documented, and formal accessibility/live deployment/root-suite/Docker evidence remains required before any physical legacy archive. See `../docs/FRONTEND_REFLEX_FINAL_AUDIT.md`.

## Final cutover cleanup status

Reflex is the preferred primary migration frontend, but the final destructive cleanup gate did not pass. The legacy Next.js frontend remains in `../frontend/` for rollback until root-suite, Docker, Market ownership, deployment-reference, and accessibility-evidence blockers are resolved.

## Old frontend removal sweep (2026-06-29)

Reflex passed local verification (`ruff`, `mypy`, `pytest`, and `reflex export`) after theme/layout repairs. It remains the preferred primary migration frontend, but not a deletion-complete production claim: the old Next.js `../frontend/` directory was kept because repository-level gates failed. Market remains partial/delegated to FastAPI/Jinja for detail/dashboard routes. See `../docs/OLD_FRONTEND_REMOVAL_REPORT.md`.
