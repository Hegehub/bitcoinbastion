# Prompt 1A-R/25 — Authority Triage Result

Status: **Ready for Prompt 1B** under the revised HTTP-only Stage-1 gate. Deferred blockers are not PASS.

## Exact baseline

The run started at `13bbc1ca60d6cc398526a0c54992e81e7a0997d1` on branch `work`, with no configured remotes and a clean worktree. Revision-bound artifacts were regenerated before classification.

## Blocker transition

| Blocker | Before | After | Re-entry / owner |
|---|---|---|---|
| P1R2-B01 | OPEN; duplicate active UI compatibility identity | RESOLVED by safe non-UI deferment of `GET /market-time-machine`; canonical `/market/time-machine` remains independently eligible | Prompt 25; API owner must establish compatibility ownership and removal policy |
| P1R2-B02 | OPEN; Access freeze mutation lacks security semantics | RESOLVED by fail-closed `DEFERRED_WITH_REASON` / `DEFERRED_AUTHORITY` | Prompt 17; Access owner must specify and test complete security/reconciliation contract |
| P1R2-B03 | OPEN; disabled login was UI optional | RESOLVED as deferred non-active legacy auth | Prompt 25; removal after compatibility window |
| P1R2-B04 | OPEN; disabled registration was UI optional | RESOLVED as deferred non-active legacy auth | Prompt 25; removal after compatibility window |
| P1R2-B05–B13 | OPEN; nine unversioned WebSocket families | DEFERRED_TO_PROMPT_4; no version invented and no runtime use allowed before resolution | Prompt 4 hard authority gate |
| P1R2-B14 | OPEN; architecture coupled to ambiguous protocols | RESOLVED for authoritative HTTP: generated typed descriptors over one shared injectable transport | Prompt 1B generates complete strict bindings and Feature 53 |

## Deterministic sets

Runtime contains 369 HTTP operations. Before triage, 313 were UI-disposed. Four operations were removed from active UI disposition, leaving `HTTP_AUTHORITATIVE_UI_SET = 309`. Deferred HTTP authority contains four records: one compatibility identity, one Access security contract, and two disabled legacy-auth routes. Nine WebSocket families are separately deferred to Prompt 4.

`01_HTTP_CLIENT_OWNERSHIP_INPUT.json` assigns exactly one generated descriptor owner to every authoritative UI HTTP operation and zero owners to deferred HTTP. It records each deferred WebSocket with `wire_version_authority = unavailable`; Prompt 1B must not invent a version.

## Stage boundary

Prompt 1B owns generated HTTP contracts, strict bindings, safe HTTP transport and Feature 53. Prompts 2 and 3 may consume only authoritative HTTP contracts. Prompt 4 first resolves B05–B13 at the wire-contract source, then owns connection lifecycle, reconnect, heartbeat and fallback.

## Rollback

Revert the generator, ownership input, architecture decision, matrices, tests and plan together. Rollback must restore the four HTTP blockers as active blockers rather than generic client owners and must retain B05–B13 as unresolved; it must never synthesize WebSocket versions or reactivate legacy auth.
