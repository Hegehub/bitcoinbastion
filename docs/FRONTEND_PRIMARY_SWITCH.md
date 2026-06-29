> Current note (2026-06-29): the old Next.js frontend has been removed; historical references below are retained only for migration context. Reflex is the only repository-native frontend.

# Frontend Primary Switch — Prompt 21/22

## 1. Executive summary

Switch decision: **SWITCH_PARTIAL_WITH_DELEGATED_ROUTES**.

The Reflex frontend is approved as the preferred primary frontend entrypoint for migration deployments because the Reflex build/export, route, navigation, safety, API-client, and test gates passed locally. The switch is partial because the legacy Next.js frontend remains available for rollback and the FastAPI/Jinja Market dashboard remains an allowed delegated owner for market-detail routes until the final audit/archive prompt.

No Next.js files were deleted, no FastAPI/Jinja market routes were removed, and no backend domain behavior was changed.

## 2. Current frontend ownership

| Surface | Current status | Notes |
| --- | --- | --- |
| Reflex frontend (`reflex_frontend/`) | Preferred primary migration entrypoint | Exposed on port `3001` in Reflex compose modes. Runtime profile metadata now marks Reflex as primary for `reflex` and `parallel` modes. |
| Legacy Next.js (`frontend/`) | Supported rollback surface | Still available on port `3000` in parallel mode and via the `nextjs` runtime mode. |
| FastAPI/Jinja Market (`app/web/`) | Delegated market-detail owner where needed | `/market`, `/market/time-machine`, `/market/{section}`, `/intelligence/timeline`, `/evidence/{packet_id}`, and `/candles/{candle_id}` remain active backend-rendered routes. |
| FastAPI API (`app/api/`) | Source of backend data | Reflex uses `BB_API_BASE_URL`; no production URL is hardcoded. |

## 3. Reflex parity gate status

| Gate | Status | Evidence | Decision |
| --- | --- | --- | --- |
| Build/export | PASS | `uv sync`, ruff, mypy, pytest, and `reflex export` passed locally. | Allows Reflex primary preference. |
| Public routes | PASS | Route registry and route tests cover required public routes. | Allows switch. |
| Console routes | PASS | Console registry/tests cover required console routes; extra provider/API/Wow routes remain preview. | Allows switch. |
| Market route ownership | PARTIAL / DELEGATED | Reflex has market pages, but FastAPI/Jinja remains active and documented for market-detail routes. | Partial switch only. |
| Trace safety/API | PASS | Trace endpoints exist, clients unwrap envelopes, and safety tests pass. | Allows switch. |
| Navigation/command palette | PASS | Required navigation and command entries are present and stale `/products`/`/self-host` entries are absent. | Allows switch. |
| No-custody/sensitive input | PASS | Safety tests reject sensitive material and scan forbidden wording. | Allows switch. |
| API client contract | PASS | API client tests cover base URL, timeout, envelope handling, error normalization, and redaction. | Allows switch. |
| Accessibility/responsive baseline | PARTIAL | Baseline helpers/docs/tests exist; formal manual audit remains required before production readiness. | Does not block migration-primary switch; blocks production-compliance claims. |
| Rollback path | PASS | Runtime modes and rollback docs preserve Next.js. | Allows switch. |

## 4. Public route parity

Required Reflex public routes are implemented in the route registry: `/`, `/platform`, `/developers`, `/operations`, `/manifesto`, `/evidence`, `/status`, `/roadmap`, `/security`, `/docs`, `/check`, `/trace`, `/trace/[report_id]`, and `/trace/[report_id]/proof-packet`.

Public-route parity remains safety-first: Trace accepts public Bitcoin addresses only, pages must show advisory/no-custody copy where relevant, and stale/degraded states must not be hidden.

## 5. Console route parity

Required console routes are implemented: `/console`, `/console/trace`, `/console/evidence`, `/console/market-intelligence`, `/console/time-machine`, `/console/sovereign-grid`, `/console/policy`, and `/console/audit`.

Console pages remain operator-review and preview surfaces. They must not execute custody, signing, treasury transfers, or irreversible policy actions.

## 6. Market route ownership

Market ownership is **delegated/partial** for the controlled switch:

- Reflex owns migration-preview routes under `/market`, `/market/timeline`, `/market/time-machine`, `/market/signals`, `/market/evidence`, `/market/narratives`, and `/market/sources`.
- FastAPI/Jinja remains active for backend-rendered market detail and fallback routes such as `/intelligence/timeline`, `/evidence/{packet_id}`, and `/candles/{candle_id}`.
- Market content remains historical/advisory context only, not financial advice, not price prediction, and not a trading signal.

## 7. Trace parity status

Trace is migration-critical and passed the controlled-switch checks:

- `/check`, `/trace`, `/trace/[report_id]`, and `/trace/[report_id]/proof-packet` are registered in Reflex.
- Trace is present in public navigation, footer navigation, and command palette actions.
- Backend endpoints exist for public summary, lite address check, address report, report detail, evidence, proof packet, status, and events.
- Trace UI and tests preserve advisory-only, not-legal-verification, not-Bitcoin-consensus-proof, no-custody, and public-address-only copy.
- Sensitive material is rejected before API submission.

## 8. API parity status

The Reflex API client uses `BB_API_BASE_URL`, request timeouts, `ResponseEnvelope.data` unwrapping, transport/error normalization, and safe public messages. Trace and public endpoint parity is documented in `docs/FRONTEND_REFLEX_API_PARITY.md`.

## 9. Safety/no-custody status

No custody feature was introduced. No seed phrase, mnemonic, private key, xprv/yprv/zprv, wallet.dat, keystore, signing material, 12-word seed, or 24-word seed input is accepted by the frontend safety validation.

Forbidden wording remains blocked in Reflex tests. The blocked set covers unsafe address labels, payment-approval claims, certainty claims, and illicit-verification claims; do not reintroduce those exact phrases in UI, docs, examples, or test fixtures outside the dedicated scanner allowlist.

## 10. Accessibility/responsive status

Accessibility and responsive baseline exists, including labels, focus helpers, reduced-motion support, responsive layout helpers, and documentation. This is not a formal WCAG compliance claim; a manual accessibility audit remains required before production readiness.

## 11. Build/test/export status

See `docs/FRONTEND_REFLEX_TEST_STATUS.md` for exact commands, pass/fail/skipped status, and known root-suite blockers.

## 12. Switch decision

**SWITCH_PARTIAL_WITH_DELEGATED_ROUTES**

Reflex is now the preferred primary frontend for runtime profile `reflex` mode and the primary frontend in `parallel` migration mode. Next.js remains available as rollback and FastAPI/Jinja Market remains delegated where needed.

## 13. Switch implementation details

- `BASTION_PRIMARY_FRONTEND=reflex` and `BASTION_LEGACY_FRONTEND=nextjs` are documented in `.env.example`.
- Runtime profile metadata marks the `reflex` and `parallel` modes with `primary: reflex` and `cutover_ready: true` for this controlled migration switch.
- `nextjs` mode remains available and marked as rollback-capable.
- Compose files from Prompt 19 remain the supported way to run Reflex only, Next.js only, or both side-by-side.

## 14. Rollback procedure

Use `docs/FRONTEND_ROLLBACK.md`. The short version:

1. Set `BASTION_PRIMARY_FRONTEND=nextjs`.
2. Use the `nextjs` runtime mode or `docker-compose.yml` / legacy frontend workflow.
3. For side-by-side diagnosis, use `deploy/compose/full-parallel-frontends.compose.yaml`.
4. Verify Trace warnings and public-address-only validation after rollback.

## 15. Remaining blockers

- Root repository `python -m pytest -q` still has known non-Reflex async/test-environment failures.
- Docker is unavailable in the local agent environment, so Docker build validation is wired but not locally executed here.
- Formal accessibility/manual responsive audit is still required before production-readiness claims.
- Final Prompt 22/22 must perform the final migration audit and Next.js legacy archive plan.

## 16. Next prompt: 22/22 final migration audit

Recommended next prompt: **Prompt 22/22 — Final Reflex Migration Audit and Next.js Legacy Archive Plan**.
