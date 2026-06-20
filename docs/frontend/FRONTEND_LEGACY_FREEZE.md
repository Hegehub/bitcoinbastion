# Frontend Legacy Freeze

Date: 2026-06-19  
Status: Next.js is **legacy-supported** until Reflex parity is complete.

## 1. Summary

The current Next.js frontend in `frontend/` is frozen as a controlled legacy surface. This freeze does not delete Next.js, does not switch production traffic to Reflex, and does not migrate routes. It records the current supported state so Reflex migration work can proceed by documented parity rather than uncontrolled replacement.

Next.js remains available as rollback until Reflex reaches documented parity.

## 2. Why the Next.js frontend is being frozen

The repository has multiple frontend/web surfaces:

- `frontend/`: current Next.js public frontend and Trace UX.
- `app/web/`: current FastAPI/Jinja Market Intelligence and Market Time Machine web dashboard.
- `reflex_frontend/`: target Reflex frontend scaffold. It is present but experimental/partial and does not yet own required routes.

Freezing Next.js prevents accidental feature expansion while preserving safety fixes, route fixes, API fixes, build fixes, test fixes, and rollback capability.

## 3. What "legacy but supported" means

Legacy-supported means:

- keep the current Next.js frontend buildable and testable;
- preserve public pages, Trace, Evidence, safety warnings, command palette behavior, and API examples until Reflex parity;
- do not add major new features or make new target architecture decisions in Next.js;
- do not delete Next.js, tests, Trace, degraded/fallback states, or safety copy;
- fix critical safety/navigation/API mismatches when required;
- treat Next.js as the rollback frontend until all cutover gates pass.

## 4. Current frontend stack

- Package: `frontend/package.json`.
- Framework: Next.js 14.2.5 with App Router.
- UI/runtime: React 18.3.1, TypeScript, Tailwind CSS, Framer Motion.
- Data layer: fetch-based clients in `frontend/services/api.ts`, `frontend/services/apiClient.ts`, and `frontend/lib/api/`.
- Tests: Vitest, Testing Library, and Playwright files under `frontend/tests/`.

## 5. Current route ownership

- Next.js currently owns public/frontend routes such as `/`, `/platform`, `/developers`, `/operations`, `/manifesto`, `/evidence`, `/status`, `/roadmap`, `/security`, `/docs`, `/check`, `/trace`, `/trace/[reportId]`, and `/trace/[reportId]/proof-packet`.
- FastAPI/Jinja currently owns Market web routes including `/market`, `/market-time-machine`, `/market/time-machine`, `/market/{section}`, `/intelligence/timeline`, `/evidence/{packet_id}`, `/candles/{candle_id}`, and `/web/*` DTO/action endpoints.
- Reflex has a scaffold and component/service/state/theme directories, but the inspected `reflex_frontend/bastion_ui/routes/` directory currently contains only `__init__.py`; required Reflex route ownership is therefore not proven.

See `docs/frontend/FRONTEND_ROUTE_INVENTORY.md` and `docs/frontend/frontend-route-inventory.json` for the route snapshot.

## 6. Current known gaps

- Required final console routes are `/console/*`, while current Next.js console-like pages are `/dashboard/*` and required Reflex routes are not registered.
- Market route ownership is split: final Reflex/console targets are desired, but FastAPI/Jinja currently renders the Market pages and exposes DTO endpoints.
- Current Next.js Trace client does not call every backend Trace panel endpoint that exists (`source-summary`, `utxo-hygiene`, and `dust-radar` are backend-available but unused by the current Next.js client).
- Prompt-requested report-scoped payment endpoints do not match backend route shape; backend exposes unscoped POST endpoints under `/api/v1/trace/payment-context`, `/payment-intent/preview`, and `/destination-review`.
- Stale route files for `/products/*`, `/self-host/*`, `/citadel`, `/treasury`, `/register`, `/enterprise`, `/blog`, `/dashboard/*`, `/design-system`, and `/genesis` remain in the tree and need archive/redirect decisions after parity.
- Repository-level pytest currently has async-test environment failures and Reflex scaffold contract failures; these are documented under Verification Results.

## 7. Allowed changes during migration

- [ ] safety wording fixes
- [ ] broken route fixes
- [ ] command palette stale link fixes
- [ ] API mismatch fixes
- [ ] test fixes
- [ ] build fixes
- [ ] documentation fixes

## 8. Disallowed changes during migration

- [ ] new major feature development
- [ ] new architecture decisions
- [ ] replacing backend logic
- [ ] deleting Trace
- [ ] deleting tests
- [ ] hiding degraded/fallback states
- [ ] adding custody/signing functionality

## 9. Rollback role

Next.js remains available as rollback until Reflex reaches documented parity. It must remain in the repository and remain operational through Reflex cutover planning.

## 10. Reflex parity gates

Reflex may become primary only after:

- all required public routes exist;
- all required Trace routes exist and match backend API contracts;
- Market routes are mirrored by Reflex or explicitly delegated to FastAPI/Jinja;
- console ownership is resolved;
- command palette entries match the required final route set;
- safety copy and no-custody validation are visible and tested;
- forbidden-wording tests pass;
- API clients unwrap `ResponseEnvelope.data` consistently while supporting raw `/web/*` DTOs;
- degraded/fallback/stale states are visible;
- Reflex build/export, Docker, and CI integration pass;
- rollback strategy is documented.

## 11. Final archival criteria

Only after the parity gates pass and a separate cutover prompt approves archive work may Next.js be archived. Archival must preserve rollback evidence, route redirects or delegation rules, and test coverage history.

## Verification Results

- `python -m pytest -q`: failed in this environment with 17 failures, 865 passed, and 2 skipped. Failures include async tests that need a suitable async pytest plugin and current incomplete Reflex scaffold contract expectations.
- `cd frontend && npm install`: completed; npm reported 16 audit vulnerabilities (4 moderate, 10 high, 2 critical) and an unknown `http-proxy` config warning.
- `cd frontend && npm run typecheck`: passed.
- `cd frontend && npm run test`: passed with 9 test files and 26 tests.
- `cd frontend && npm run build`: passed and generated the Next.js app route build output.
- `python -m pytest tests/security/test_developer_layer_forbidden_wording.py -q`: passed.
