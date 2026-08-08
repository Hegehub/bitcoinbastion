# Prompt 1A/25 — Contract Authority Stop Report

Status: **BLOCKED**. Prompt 1B must not start and Feature 53 remains incomplete.

## Pre-flight

Prompt 1A started at `bbba12b5f56429f9964631e950cbe6f2bde6063f` on branch `work`, with no configured remotes and a clean worktree. HEAD differed from the preceding recorded Prompt-1 evidence, so the runtime generator and Prompt-0 validator were rerun. Runtime evidence still contains 369 HTTP operations, nine WebSocket channels, and the blockers below.

## Mandatory authority blockers

| ID | Matrix records | Authoritative source | Missing authority | Security/product impact | Smallest safe action |
|---|---|---|---|---|---|
| P1R2-B01 | `HTTP-0350`, `HTTP-0351` | stacked decorators on `app.web.routes_market:market_time_machine` | Repository navigation suggests `/market/time-machine`, but no compatibility owner, lifetime, external-consumer inventory, or removal policy authoritatively designates the other path as an alias. | Renaming or deprecating a public identity could break unknown consumers. | API owner records the canonical path and compatibility guarantee; then assign distinct explicit operation IDs and test alias equivalence. |
| P1R2-B02 | `HTTP-0006` | `app.api.v1.access:freeze_child_api_key` | Unlike adjacent key mutations, the route has no Access-session dependency; code/tests do not establish entitlement, scope, PoP/signing, Human Intent, replay, or an authoritative non-UI disposition. | Generating UI metadata would either expose an under-specified mutation or invent policy. | Access owner supplies the complete security contract or explicitly classifies the route non-UI; add security tests before generation. |
| P1R2-B03 | `HTTP-0039` | `app.api.v1.auth:login` | The active route always returns `410 Gone`, but canonical disposition generation still marks it `UI_OPTIONAL`. | A UI client would advertise superseded password/bearer authentication. | Disposition owner approves a canonical non-UI state and adds an invariant test. |
| P1R2-B04 | `HTTP-0040` | `app.api.v1.auth:register` | Same disabled legacy-auth mismatch as B03. | Same as B03. | Same as B03. |
| P1R2-B05–B13 | `WS-001`–`WS-009` | `app.api.v1.ws` and `app.services.events.websocket_serialization` | Event messages carry an event version, but system/error/heartbeat envelopes do not; arbitrary payload dictionaries have no discriminated schema, unknown-version policy, or known-consumer compatibility inventory. | Adding wire fields or rejecting versions may break unknown consumers; frontend-only version metadata would be false authority. | Event/protocol owners define a backward-compatible versioned envelope, payload registry, and unknown-version behavior with compatibility tests. |
| P1R2-B14 | all 313 UI-disposed HTTP records | current handwritten frontend clients and absent generated DTO/client family | Architecture selection depends on the unresolved identity, security, disposition, and wire contracts above. | A generator built now would encode guesses and could expose excluded operations or flatten Access security. | After B01–B13 are authoritative, approve generated typed descriptors plus a single transport engine (or document a safer repository-supported alternative), then implement the representative generator sample in Prompt 1A. |

## Decision

The Prompt-1A stop conditions explicitly require stopping when Access security cannot be proven and no authoritative non-UI disposition exists, when compatibility ownership needs an unavailable API-stability decision, or when WebSocket versioning may break unknown consumers. All three conditions are present. No backend route, security dependency, wire payload, client generator, DTO, registry, dependency, Prompt-2 adapter, or Prompt-4 lifecycle was changed.

The execution plan now records Prompt 1A and Prompt 1B as Stage-1 subgates without renumbering Prompts 2–25 or reallocating Feature 53.

## Rollback

Revert this report and the Stage-1 plan clarification together. This restores the former single Prompt-1 planning view only; it must not be interpreted as resolving the authority blockers. No runtime rollback is needed because Prompt 1A made no production contract change.
