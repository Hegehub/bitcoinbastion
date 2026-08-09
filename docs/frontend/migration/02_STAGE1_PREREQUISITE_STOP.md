# Prompt 2/25 — Stage-1 Revision Prerequisite Stop

Status: **BLOCKED before Prompt-2 implementation**.

Prompt 2 started on branch `work` at
`360e85a0825ffdfc93b68a182594963930342b96` with a clean worktree and no
configured Git remotes. The revision-bound Stage-1 inputs identify a different
source revision:

| Artifact | Recorded source revision | Current Prompt-2 starting HEAD | Result |
|---|---|---|---|
| `00_OPENAPI_SNAPSHOT.json` | `0ff0049114b864079ed7aabbc3272c82b5d9b106` | `360e85a0825ffdfc93b68a182594963930342b96` | STALE |
| `generated_manifest.json` | `0ff0049114b864079ed7aabbc3272c82b5d9b106` | `360e85a0825ffdfc93b68a182594963930342b96` | STALE |
| generated Feature-53 entries | `0ff0049114b864079ed7aabbc3272c82b5d9b106` | `360e85a0825ffdfc93b68a182594963930342b96` | STALE |

`python scripts/generate_http_transport.py --check` passes byte comparison and
`python scripts/validate_frontend_migration_baseline.py` passes structural
invariants, but neither validator currently requires the recorded source
revision to equal `git rev-parse HEAD`. Therefore those successes do not satisfy
Prompt-2 prerequisite P2-A01.

## Required Stage-1 remediation

Return ownership to Stage 1 and regenerate/bind the OpenAPI snapshot, migration
matrix, generated manifest, generated schemas, generated HTTP bindings,
ownership registry and Feature-53 entries to one explicitly defined source
revision policy. Add a validator that compares that policy to the checked-out
revision (or to a documented source-tree digest that is not self-referential).
Only after that validator passes may Prompt 2 consume generated DTOs.

## Deliberately not implemented

No Prompt-2 domain adapter, view model, provenance enum/badge, request lifecycle,
Reflex State, component, fixture, browser harness or coverage promotion was
created. WebSocket B05-B13 remain deferred to Prompt 4.

## Rollback

Revert this report and its index link only. Stage-1 generated artifacts and all
runtime/frontend behavior remain unchanged.
