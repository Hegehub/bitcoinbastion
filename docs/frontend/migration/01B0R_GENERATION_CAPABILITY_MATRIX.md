# Prompt 1B0-R/25 — Full-Set Preflight and Stop Report

Status: **BLOCKED**. Prompt 1B1 must not start.

## Exact baseline

The corrective run started at `b88e63fd23d189030ee7a89ac9318514677db6c0` on branch `work`, with no configured remotes and a clean worktree. Runtime OpenAPI and the fail-closed ownership matrix were recalculated rather than trusting the prior summary.

## Deterministic full-set preflight

`python scripts/analyze_http_generation_preflight.py --write|--check` scans all 309 candidates without generating clients. It records each protected operation and mutation by stable matrix/operation identity, inventories schema keywords and response media/status classes, and emits stable B01/B02 diagnostics. It never treats OpenAPI security presence as complete semantic authority and never invents WebSocket versions.

| Measure | Count |
|---|---:|
| Runtime HTTP operations | 369 |
| UI generation candidates | 309 |
| Protected candidates | 65 |
| Mutation candidates | 65 |
| Candidates blocked by reviewed security | 65 |
| Candidates blocked by mutation authority | 65 |
| Candidates free of B01/B02 (not necessarily generator-ready) | 200 |
| Unproven used schema capabilities | 2 (`additionalProperties`, `anyOf`) |

Protected and mutation sets overlap, so blocker counts are not additive.

## Schema vocabulary

The machine artifact contains exact counts and examples for `$ref`, primitive/object/array types, formats, enums, `anyOf`, `additionalProperties`, bounds, patterns, defaults, deprecation, nullable, and read/write annotations found in candidate operations. The current fixed-schema foundation does not strictly generate the two commonly composed constructs `anyOf` and `additionalProperties`; B03 remains open. No fallback to `Any` was added.

## Response vocabulary

| Class | Count |
|---|---:|
| JSON success | 300 |
| HTML/text success | 6 |
| Explicit 204/no-content | 3 |
| 200 success | 305 |
| 201 success | 1 |
| 204 success | 3 |

No candidate currently exposes binary or streaming success media through OpenAPI. Text/HTML and first-class no-content still require generator coverage beyond the two-operation foundation.

## Blocker results

* **P1B0-B01 remains OPEN:** 65 protected candidates lack reviewed operation-level scope, PoP/session, signed-request, origin-binding, Human Intent, step-up, replay, audit, and revocation projection. The stop rule prohibits inferring these from OpenAPI or neighboring routes.
* **P1B0-B02 remains OPEN:** 65 mutations lack complete source-backed idempotency, retry, replay, Human Intent, timeout/reconciliation, and audit classification. HTTP method alone is not authority.
* **P1B0-B03 remains OPEN:** the generator lacks strict full-vocabulary support for used `anyOf` and `additionalProperties` schemas and does not yet generate HTML/text or all 204 contracts.
* **B05–B13 remain deferred to Prompt 4:** no WebSocket version or runtime behavior was introduced.

## Smallest safe next actions

1. Backend security owners publish a tested operation-level security projection for the 65 protected candidates.
2. Domain owners publish a tested mutation-safety/idempotency/Human-Intent registry for the 65 mutations.
3. Extend the DTO generator with strict reviewed map and nullable/union policies plus text and no-content handlers, then rerun this preflight until every blocker count is zero.

## Rollback

Remove the preflight script, JSON artifact, invariant test, and this report together. The existing fail-closed client ownership and Prompt-4 WebSocket blockers remain authoritative. Rollback must not reinterpret candidates as generated clients or introduce permissive `Any`, retry, or security defaults.
