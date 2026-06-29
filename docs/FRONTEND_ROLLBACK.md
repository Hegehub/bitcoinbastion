> Current note (2026-06-29): the old Next.js frontend has been removed; historical references below are retained only for migration context. Reflex is the only repository-native frontend.

# Frontend Rollback Guide

## 1. When to rollback

Rollback to the legacy Next.js frontend if Reflex export fails in CI, Trace safety copy regresses, required public/console routes disappear, degraded-state visibility is lost, operators report severe accessibility/responsive issues, or the FastAPI API contract changes before Reflex adapters are updated.

## 2. How to switch primary frontend back to Next.js

Set the runtime/frontend selector back to Next.js:

```bash
export BASTION_PRIMARY_FRONTEND=nextjs
export BASTION_LEGACY_FRONTEND=nextjs
```

Then use the `nextjs` runtime profile metadata or the existing legacy frontend workflow. Runtime profile metadata keeps `nextjs` mode available with rollback enabled.

## 3. How to run legacy Next.js locally

```bash
cd frontend
npm install
npm run dev
```

The legacy frontend listens on port `3000` by default and uses `NEXT_PUBLIC_API_BASE_URL` for FastAPI API access.

## 4. How to run Reflex locally

```bash
cd reflex_frontend
uv sync
uv run reflex run --env dev
```

Reflex migration compose mode exposes the frontend on port `3001` and its backend/control port on `8001`.

## 5. How to run both side-by-side

```bash
docker compose -f deploy/compose/full-parallel-frontends.compose.yaml up -d --build
```

Expected ports:

- FastAPI API: `8000`
- legacy Next.js: `3000`
- Reflex frontend: `3001`
- Reflex backend/control: `8001`

## 6. How market routes are handled

Market route ownership remains delegated/partial. Reflex provides migration-preview Market pages, while FastAPI/Jinja market routes under `app/web/` remain active for detail and fallback routes such as `/intelligence/timeline`, `/evidence/{packet_id}`, and `/candles/{candle_id}`.

## 7. How to verify Trace after rollback

Run the legacy and Reflex Trace checks where practical:

```bash
cd frontend
npm run test -- trace-api-contract.test.ts
cd ../reflex_frontend
uv run pytest bastion_ui/tests/test_trace_safety.py bastion_ui/tests/test_no_sensitive_input.py
```

Manually confirm that `/check`, `/trace`, Trace report pages, and Proof Packet pages remain advisory-only, no-custody, not legal verification, not Bitcoin consensus proof, and public-address-only.

## 8. Known limitations

- Rollback changes frontend preference only; it does not change backend domain behavior.
- Docker readiness depends on the host Docker environment.
- The root pytest suite still contains known async/test-environment blockers unrelated to the Reflex switch.
- Rollback must not introduce custody, signing, seed/private key, wallet file, or keystore handling.
