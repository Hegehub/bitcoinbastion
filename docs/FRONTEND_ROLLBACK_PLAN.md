# Frontend Rollback Plan

## 1. When rollback is allowed

Rollback is allowed whenever Reflex export/build fails, route/API parity regresses, Trace safety copy regresses, sensitive-input rejection fails, operators find severe accessibility/responsive issues, Market delegation breaks, or production incident response requires the known legacy surface.

## 2. How to point routes back to Next.js

Set frontend selection back to Next.js and use the legacy runtime mode:

```bash
export BASTION_PRIMARY_FRONTEND=nextjs
export BASTION_LEGACY_FRONTEND=nextjs
```

Then run the legacy frontend from `frontend/` or choose the `nextjs` runtime profile.

## 3. How to point routes back to FastAPI/Jinja Market dashboard

Keep FastAPI running and route Market traffic to the backend-rendered routes under `app/web/routes_market.py`, including `/market`, `/market/time-machine`, `/market/{section}`, `/intelligence/timeline`, `/evidence/{packet_id}`, and `/candles/{candle_id}`.

## 4. How to disable Reflex frontend

Stop the Reflex service in compose/runtime mode or switch from `reflex`/`parallel` to `nextjs` or `api-only` mode. Do not remove Reflex files during emergency rollback.

## 5. How to verify Trace after rollback

- Open `/check` and `/trace` in the rollback frontend.
- Confirm public-address-only validation.
- Confirm advisory-only, no-custody, not legal verification, and not Bitcoin consensus proof copy remains visible.
- Run legacy Trace API contract tests and Reflex safety tests if both surfaces are available.

## 6. How to verify Market after rollback

- Open `/market` and `/market/time-machine` from FastAPI/Jinja.
- Confirm historical/advisory limitations remain visible.
- Confirm evidence/candle/detail drill-down links render or degrade visibly.

## 7. How to verify safety copy after rollback

Run the focused safety/forbidden wording tests where available and manually inspect Trace, Proof Packet, Market, and Console copy. No route may request custody material, signing material, wallet files, keystores, private keys, mnemonic-like phrases, or extended private keys.

## 8. Known rollback limitations

- Rollback changes frontend ownership only; it does not alter backend domain behavior.
- Docker/compose rollback depends on host Docker availability.
- FastAPI/Jinja Market remains intentionally active during migration.
- Root pytest still has known non-Reflex/root-suite blockers that should be fixed independently.
- Rollback must not introduce custody, signing, mining, Stratum, or backend-mesh behavior.

## Final cutover cleanup note (2026-06-28)

The destructive removal gate did not pass, so rollback still uses the intact `frontend/` directory. Do not remove this directory from operational deployments until the full cutover audit blockers are cleared and maintainers approve losing the runnable Next.js fallback.
