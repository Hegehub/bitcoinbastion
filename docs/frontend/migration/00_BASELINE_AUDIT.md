# Prompt 0/25 — Current-HEAD Source-of-Truth Baseline Audit

## Baseline identity and evidence classification

- **Verified current fact:** branch `work`, HEAD `63538ae5788b1df924f1aa459e500891011ed83a`; no configured remotes; starting worktree clean. Repository root is `/workspace/bitcoinbastion` and no applicable `AGENTS.md` was present.
- **Generation:** `python scripts/generate_frontend_migration_audit.py`, Python 3.12.13, `app.core.config` defaults, timestamp recorded inside the generated snapshot. Runtime import emitted four FastAPI duplicate-ID warnings; the normalized final contract contains one duplicate ID.
- **Preservation:** the historically reported `bitcoin_bastion.db-journal` is absent at this checkout. No pre-existing changed or untracked files were found, so there was no unrelated user content to touch.
- **Historical comparison seed:** the prior documents were generated against parent `ee2792fe4397184f9d6f068b7cee7c2b19fe17e8`. Prompt 1–3 implementation results do not occur after the baseline merge in current Git history; only the Prompt-0 baseline commit and merge are present.

## Runtime contract result

Runtime `app.openapi()` contains **351 paths, 369 HTTP operations, 319 `/api/v1` paths, 337 `/api/v1` operations, 286 component schemas, and six security schemes**. Actual registered `ws_router.routes` contains **9 WebSocket channels**. The duplicate final operation ID is `market_time_machine_market_time_machine_get`. Counts are unchanged from the prior snapshot; semantic snapshot deltas are baseline metadata (HEAD/branch/timestamp/security-scheme inventory) and reassignment of implementation prompts from 0–52 to 1–25. No backend route, schema, policy, storage, dependency, or runtime behavior changed.

Disposition across HTTP and WebSocket records is: **UI_REQUIRED 264, UI_OPTIONAL 58, CALLBACK_ONLY 18, PROTOCOL_ONLY 25, SEPARATE_PRODUCT 13**. Coverage is conservatively **NOT_STARTED 335** and **NOT_APPLICABLE 43**. Every one of the 378 runtime records has one stable matrix ID and one disposition. The generated matrix is operation-complete planning evidence, but dependency-level auth, source-symbol ownership, exact error semantics, client/adapter/trigger/render and browser proof remain explicitly unverified per record.

## Transformation and frontend inventory

Source inventory finds **29 State classes, 174 async method declarations, 19 client classes, 152 `dict[str, Any]` declarations, 68 distinct production API literals (53 matching; 15 stale/absent), zero `on_load` occurrences, and zero `rx.foreach` occurrences**. Because no executed ownership analyzer exists at HEAD, duplicate-adapter, unowned-view-model, compatibility-wrapper, and unsafe-serialization counts are **UNAVAILABLE (not zero)**; this is a B0 limitation and Prompt 1 must add AST/consumer ownership evidence before any coverage promotion. Existing route/workflow matrices preserve route, dynamic-parameter, pagination, placeholder, subscription/fallback and privacy unknowns rather than guessing.

## Strict implementation and provenance

`IMPLEMENTED_VERIFIED` requires: current runtime contract → auth/security contract → typed client → typed safe adapter/view model → explicit lifecycle trigger → named field rendering → all required failure/degraded states → privacy controls → contract test → browser network/DOM/accessibility evidence. Registration, DTOs, clients, State, fixtures, static components, mock tests and source strings are insufficient.

The only provenance states are `LIVE`, `VERIFIED_SNAPSHOT`, `DEMO_FIXTURE`, and `UNAVAILABLE`. Mixed-source screens use section-level provenance. Provenance never asserts correctness, health, freshness, confidence, authorization, Evidence verification, or Bitcoin consensus validity.

## Frozen decisions G1–G18

| Gate | Decision |
|---|---|
| G1 | Exact-HEAD runtime `app.openapi()` and registered `ws_router.routes` are contract truth; normalized generated snapshot is evidence. |
| G2 | Every operation/channel has exactly one disposition and explicit product boundary; callback/protocol routes are not generic actions. |
| G3 | The complete request-to-render chain above is the sole verified implementation definition. |
| G4 | Generated DTO/client → domain-owned safe adapter/view model → State → component; imports never reverse and raw envelopes never render. |
| G5 | Named route load/user event/poll/subscription, cancellation, visibility pause and teardown are mandatory evidence. |
| G6 | Payment proof, entitlement, issuer right, device possession, PoP, signing, scope, policy, Human Intent, revocation and recovery stay distinct; one-time secrets are ephemeral reveal/copy/acknowledge only. |
| G7 | Exactly four provenance states; degraded/freshness/confidence remain orthogonal. |
| G8 | Route/component registry and per-surface flags own navigation; capability visibility makes no unsupported RBAC claim. |
| G9 | Retain `/console/wow`; redirect only after ownership, live/unavailable view models, telemetry and compatibility proof; removal requires a later explicit gate. |
| G10 | Surface role (shell/panel/reading/critical) and finish (clear/matte/solid) are independent; one blur depth and warm-neutral solid/static downgrade. |
| G11 | URL/storage/telemetry/clipboard/share are default-deny, field-specific allowlists; secrets and raw errors are always denied. |
| G12 | HTTP retries are bounded/idempotent-only; WS uses heartbeat, bounded jittered reconnect, visible stale state and explicit HTTP fallback/unavailable replay. |
| G13 | Contract tests plus browser network/DOM/a11y and visual evidence at 1440×900 and 430×932; source and mocks alone are insufficient. |
| G14 | No visualization dependency is approved; license, CSP, supply chain, bundle/export and reversible fallback approval is required. |
| G15 | Existing job runtime remains canonical; any future Temporal is an external optional service boundary, never frontend truth. |
| G16 | PayRegister remains independently flagged, routed and navigated as a separate merchant product. |
| G17 | The owner-supplied catalog in this Prompt is reconciliation authority; old working labels are retained in the register audit column, never as alternate ID meanings. |
| G18 | `00_EXECUTION_PLAN_0_25.md` is canonical; 0–52 remains marked superseded and retains unique history. Generated matrices are regenerated, not hand-edited. |

## B0 gate and rollback

The contract, disposition uniqueness, approved feature count/names/owners and prompt mapping gates pass. **Prompt 1 may start only as contract/client/ownership work; no UI item is currently verified.** Residual blocker: ownership/auth semantics and transformation totals are not mechanically complete, and browser forced-state evidence is unavailable. This does not block Prompt 1's explicitly assigned work but blocks any implementation promotion.

Rollback planning-only changes with a normal revert commit. To restore the old view temporarily, relink the superseded 0–52 file; never alter approved feature meanings. A single generated matrix can be regenerated from the retained exact snapshot/generator revision. Link rollback must not touch `app/`, frontend runtime files, schemas, policy, storage or dependencies; prove this with `git diff --name-only <before>..<after>` and runtime snapshot comparison.
