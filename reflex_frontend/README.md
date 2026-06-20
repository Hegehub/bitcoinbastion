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
