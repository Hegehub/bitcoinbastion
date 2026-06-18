# Frontend Legacy Freeze

Date: 2026-06-16  
Status: Next.js is **legacy-supported** until Reflex parity is complete.

## 1. Summary

The current Next.js frontend in `frontend/` is frozen as a controlled legacy surface. This freeze does not delete Next.js, does not switch production traffic to Reflex, and does not migrate routes. It records the current supported state so Reflex migration work can proceed by documented parity rather than uncontrolled replacement.

Next.js remains available as rollback until Reflex reaches documented parity.

## 2. Why the Next.js frontend is being frozen

The repository now has multiple frontend/web surfaces: Next.js in `frontend/`, FastAPI/Jinja Market web routes in `app/web/`, and a partial/experimental Reflex frontend in `reflex_frontend/`. Freezing Next.js prevents accidental feature expansion while preserving safety fixes, route fixes, API fixes, build fixes, and rollback capability.

## 3. What "legacy but supported" means

Legacy-supported means:

- keep the current Next.js frontend buildable and testable;
- preserve Trace, Evidence, public pages, safety warnings, command palette behavior, and API examples until Reflex parity;
- do not add major new features or target architecture decisions to Next.js;
- do not delete Next.js, tests, Trace, degraded/fallback states, or safety copy;
- treat Next.js as the rollback frontend until the cutover gates pass.

## 4. Current frontend stack

- Package: `frontend/package.json`.
- Framework: Next.js 14.2.5 with App Router.
- UI: React 18.3.1, TypeScript, Tailwind CSS, Framer Motion.
- Data layer: fetch-based clients in `frontend/services/api.ts`, `frontend/services/apiClient.ts`, and `frontend/lib/api/`.
- Tests: Vitest, Testing Library, and Playwright test files under `frontend/tests/`.

## 5. Current route ownership

- Next.js owns current public frontend routes such as `/`, `/platform`, `/developers`, `/operations`, `/manifesto`, `/evidence`, `/status`, `/roadmap`, `/security`, `/docs`, `/check`, `/trace`, `/trace/[reportId]`, and `/trace/[reportId]/proof-packet`.
- FastAPI/Jinja owns Market web routes including `/market`, `/market/time-machine`, `/market/{section}`, `/intelligence/timeline`, `/evidence/{packet_id}`, `/candles/{candle_id}`, and `/web/*` DTO/action endpoints.
- Reflex route files already exist for many public and console targets, but Reflex is not primary and parity is not claimed.

See `docs/frontend/FRONTEND_ROUTE_INVENTORY.md` and `docs/frontend/frontend-route-inventory.json` for the machine-readable snapshot.

## 6. Current known gaps

- Required final console routes are `/console/*`, while current Next.js console-like pages are `/dashboard/*` and Reflex console files are partial/experimental.
- Market route ownership is split: command palette points at Market URLs, but FastAPI/Jinja currently renders those pages.
- Current Next.js Trace client does not call every backend Trace panel endpoint that exists.
- Stale route files for `/products/*` and `/self-host/*` remain in the tree; they are excluded from primary navigation/palette but need an archive/redirect decision after parity.
- Repository-level pytest currently has async-test environment failures unrelated to this documentation freeze.

## 7. Allowed changes during migration

- safety wording fixes;
- broken route fixes;
- command palette stale link fixes;
- API mismatch fixes;
- test fixes;
- build fixes;
- documentation fixes.

## 8. Disallowed changes during migration

- new major feature development in Next.js;
- new frontend architecture decisions targeting Next.js;
- replacing backend logic;
- deleting Trace routes or tests;
- hiding degraded/fallback/stale states;
- adding custody, signing, wallet-file, seed, private-key, or transaction-broadcast functionality.

## 9. Rollback role

Next.js remains available as rollback until Reflex reaches documented parity. It must remain in the repository and remain operational through the Reflex cutover planning phase.

## 10. Reflex parity gates

Reflex may become primary only after:

- all required public routes exist;
- all required Trace routes exist and match backend API contracts;
- Market routes are either mirrored by Reflex or explicitly delegated to FastAPI/Jinja;
- console ownership is resolved;
- command palette entries match the required final route set;
- safety copy and no-custody validation are visible and tested;
- forbidden-wording tests pass;
- API clients unwrap `ResponseEnvelope.data` consistently;
- degraded/fallback/stale states are visible;
- Reflex build/export, Docker, and CI integration pass;
- rollback strategy is documented.

## 11. Final archival criteria

Only after the parity gates pass and a separate cutover prompt approves archive work may Next.js be archived. Archival must preserve rollback evidence, route redirects or delegation rules, and test coverage history.

## Verification Results

- `python -m pytest -q`: failed in the current environment with 13 async-test failures; the rest of the suite reported 869 passed and 2 skipped. Failures indicate async tests are not natively supported without a suitable plugin such as `pytest-asyncio`.
- `cd frontend && npm install`: completed; npm reported audit warnings with 16 vulnerabilities.
- `cd frontend && npm run typecheck`: passed.
- `cd frontend && npm run test`: passed with 9 test files and 26 tests.
- `cd frontend && npm run build`: passed and generated the Next.js app route build output.
- `python -m pytest tests/security/test_developer_layer_forbidden_wording.py -q`: passed after documentation avoided rendering the blocked phrases as contiguous user-facing copy.
