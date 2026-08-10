# Prompt 1B0-R2/25 — Corrected Foundation Gap Report

Status: **BLOCKED**. Prompt 1B1 must not start.

## Baseline and corrected inventory

The run started at `7c8da903097de9921bccce322f579b522e83ba03` on branch `work`, with no configured remotes and a clean worktree. The prior schema scan counted only inline operation fragments and did not resolve component `$ref` graphs. The preflight now follows nested/recursive component references with per-operation cycle detection.

| Set | Count |
|---|---:|
| Generation candidates | 309 |
| Protected | 65 |
| Mutations | 65 |
| Protected-only | 44 |
| Mutation-only | 44 |
| Protected mutations | 21 |
| Unique B01/B02 operations | 109 |
| Free of B01/B02 (not fully ready) | 200 |

## B01 and B02

Both remain open. Current repository evidence still does not establish complete scope, PoP/signing, origin, Human Intent, step-up, replay, audit, revocation, idempotency, retry, or reconciliation semantics for all affected operations. The stop conditions forbid creating reusable profiles from URL prefixes, methods, or neighboring routes. The generated JSON retains every affected operation and its stable blocker.

## Corrected schema vocabulary

Resolving component graphs reveals 903 refs, 562 `anyOf` occurrences, 291 `additionalProperties` occurrences, 54 enums, two consts, 221 formats, 757 arrays, 1,315 objects, and all recorded bounds/defaults across candidate operation graphs. These are occurrence counts, not unique schemas. `anyOf` and `additionalProperties` therefore remain full-generator blockers; the previous inline-only counts understated their reach.

The transport foundation now provides an explicit recursive JSON value type rather than Python `Any`, but the generator does not yet classify each of the 291 map occurrences as closed, typed, or reviewed arbitrary JSON. It likewise does not yet compile the 562 `anyOf` occurrences into nullable or strict union forms.

## Response capabilities

The runtime inventory remains 300 JSON, six `text/html`, and three 204 successes; no `text/plain`, binary, or streaming success response appears in the candidate OpenAPI set. The shared transport now supports:

* first-class `NoContentDTO`, rejecting unexpected 204 bodies and remaining distinct from 200-null;
* typed `TextResponseDTO` with content-type enforcement (capability present, current usage zero);
* opaque `OpaqueHtmlDocumentDTO` with content-type enforcement and no trusted/raw DOM behavior.

These transport capabilities do not close B03 because the generator still emits only two fixed JSON foundation operations and has not classified/generated the six HTML or three 204 operations.

## Residual blockers

* **P1B0-B01:** 65 protected operations lack complete authoritative security projection.
* **P1B0-B02:** 65 mutations lack complete authoritative mutation/Human-Intent/idempotency projection.
* **P1B0-B03:** strict per-schema `anyOf` and `additionalProperties` compilation plus generated HTML/204 operation coverage remain incomplete.
* **B05–B13:** remain deferred to Prompt 4; no WebSocket work was introduced.

## Rollback

Revert the ref-resolving preflight, updated artifact/test, special-response DTO/transport handlers, tests, and this report independently. Rollback must restore those capabilities to blocked status and must not introduce `Any`, trusted HTML, fabricated 204 bodies, automatic mutation retry, or inferred security profiles.
