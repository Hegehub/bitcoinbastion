# Prompt 0/52 — Source-of-Truth Baseline Audit

## Baseline identity

- **Working revision:** `ee2792fe4397184f9d6f068b7cee7c2b19fe17e8` on branch `work`.
- **Snapshot command:** `python scripts/generate_frontend_migration_audit.py` from repository root, Python 3.12, current `app.core.config` defaults.
- **Runtime contract:** 351 paths, 369 HTTP operations; 319 `/api/v1` paths and 337 `/api/v1` operations; 286 component schemas; 9 registered WebSocket channels.
- **Known contract defect:** duplicate `market_time_machine_market_time_machine_get`; FastAPI also warns that three market handlers share function-derived IDs even though their final IDs differ by path.
- Historical revisions and counts in the prompt are comparison seeds only. This checkout is the baseline.

## Evidence hierarchy

1. `app.openapi()` and the actual `ws_router.routes` registrations at this revision.
2. Router dependencies, schema code, policy services and security tests.
3. Executed client/State/adapter/component contract tests.
4. Browser network, DOM, accessibility and visual evidence.
5. Documentation and source searches (leads only, never parity proof).

## Frontend gap findings

The audit found 68 distinct production frontend API literals: 53 resolve to the runtime OpenAPI and 15 are stale/absent (see `00_FRONTEND_URL_AUDIT.json`). Source inspection finds no `on_load=` and no `rx.foreach`; many async State and client methods exist, but only explicit event wiring plus runtime network/DOM evidence can promote coverage. The legacy parity checker labels route registration and source substrings “implemented”; it therefore overstates request-to-render parity.

Conservative baseline coverage is **NOT_STARTED for every UI-disposed runtime operation/channel**. This is not a claim that no code exists: it records that the required ten-link chain (contract, auth, typed models, adapter, trigger, named rendering, state handling, privacy, contract test, browser evidence) has not been proven operation by operation. Existing clients and States are candidates for Prompt 1 verification, not credited implementation.

## Product and security decisions

- Python/Reflex remains the sole repository-native frontend. FastAPI/domain services/canonical stores remain business truth.
- Proof-of-Access is not a password or bearer shortcut. Wallet proof, entitlement, device possession, PoP session, request signing, scope, policy, revocation, recovery and Human Intent remain distinct.
- No signing, broadcasting, custody, automatic treasury/recovery/blocking, or secret/private-key collection is UI scope.
- Trace remains advisory/public-data-only; Market remains informational. Unknown, stale, partial, conflicting, degraded, synthetic, fallback and offline provenance must remain visible.
- PayRegister is `SEPARATE_PRODUCT`, gated by `payregister_ui`, with no core navigation entry. LNURL callbacks and protocol handshakes remain backend owned.
- `/console/wow` is retained until domain components have live/unavailable view-models, primary owners, tests, compatibility evidence and removal gates.

## Strict parity definition

`IMPLEMENTED_VERIFIED` requires all ten links specified by Prompt 0. Route registration, a client method, populated State, placeholder, fixture preview, source-string test, or mock deserialization cannot independently satisfy parity. Coverage promotions are performed only by the matrix validator introduced in Prompt 1.

## Privacy allowlist and denylist

**Allowed when non-sensitive:** public route slug; documented filter/sort/page cursor; public report/packet identifier explicitly classified shareable; display preferences (theme, reduced motion/transparency); provenance mode. URLs, telemetry, clipboard and share links each require a field-specific allow decision.

**Denied everywhere persistent or ambient:** seed/mnemonic, private or extended private key, WIF, wallet file/keystore/signing material; session/PoP/request signatures/nonces; one-time credentials; child-key/delegated-pass secret; recovery factors; payment preimages; raw rejected input. One-time values use controlled reveal/copy/acknowledgement, never automatic persistence. Deterministic fixtures contain only clearly synthetic public data.

## Decision gates

| Gate | Outcome |
|---|---|
| G1 | Runtime `app.openapi()` plus registered `ws_router.routes`, pinned snapshot and revision. |
| G2 | Exactly-one record and reason in the JSON matrix; dispositions are conservative and require owner review. |
| G3 | Ten-link strict parity definition adopted; old parity script is non-authoritative. |
| G4 | Generated DTO/client layer → domain adapter/view-model → State → component; no raw envelope rendering. |
| G5 | Explicit route load, user submit/click, bounded polling or subscription; cancellation and visibility pause required. |
| G6 | PoA/PoP/signing/scope/Human Intent preserved; one-time secrets controlled and non-persistent. |
| G7 | Every view model carries `LIVE`, `VERIFIED_SNAPSHOT`, `DEMO_FIXTURE`, or `UNAVAILABLE`; never silent fallback. |
| G8 | Five core screens own core navigation; capability gates hide/disable honestly; PayRegister separate. |
| G9 | Retain `/console/wow`; redirect/remove only after compatibility and domain extraction evidence. |
| G10 | Role and finish independent; one blur depth, solid critical/reading fallback and adaptive GPU budget. |
| G11 | Explicit safe-field allowlist above; default deny for URL/storage/telemetry/clipboard/share. |
| G12 | Bounded jittered reconnect, visible stale timer, heartbeat, HTTP fallback; replay unavailable is explicit. |
| G13 | Playwright-like network+DOM+a11y evidence at 1440×900 and 430×932; screenshots supplement assertions. |
| G14 | No dependency approved in Prompt 0; license, CSP, supply-chain, bundle, SSR/export and rollback gate required. |
| G15 | Existing Celery/runtime stays canonical; any future Temporal integration is an optional service adapter, never frontend state. |
| G16 | PayRegister uses its own feature flag, route family, merchant actor and navigation boundary. |

## Blockers and owner decisions

The immutable approved 69-feature pack is not present under that name in this checkout; the register preserves IDs and maps a non-renumbered working catalog, flagged for product-owner label reconciliation before Prompt 9. OpenAPI does not express every dependency-level authorization nuance or WebSocket security contract; Prompts 1, 4 and 5 must bind source dependencies and security tests. Browser forced-state evidence is blocked until a deterministic interception harness exists. Prompt 1 may start on generated contract ownership, but no UI implementation may claim parity until these gates close.
