# Prompt 1B0-R5/25 — General Schema Compiler Result

Status: **BLOCKED**. A general normalized schema compiler now exists, but full source emission and eight active backend `Any` contracts remain unresolved.

## Baseline

The run started at `3ca9727dfe52274ccee929e1373dc52fe16f2232` on branch `work`, with no remotes or unrelated changes.

## Compiler implementation

`bastion_ui.transport.schema_compiler.OpenAPISchemaCompiler` replaces selected-schema semantics for normalization. It provides deterministic IR nodes for primitives, null, refs, arrays, objects, properties with requiredness, literals/enums, unions, typed maps, closed objects, and explicit recursive JSON maps. It builds a sorted component dependency graph, detects cycles, resolves refs, recursively compiles nested `anyOf` and `additionalProperties`, preserves constraints, and fails explicitly on absent schema meaning.

The current OpenAPI has 286 component schemas and no component-reference cycles. The compiler normalizes 271. It processes 68 of 76 `anyOf` components and 68 of 76 `additionalProperties` components. The remaining failures are not compiler-architecture gaps: backend models expose `Any`/empty schemas with no type contract.

## Exact source-contract failures

| Component | Exact missing schema | Active consumers |
|---|---|---|
| AccessCertificateIssueResponse | `expires_at: Any` | none; mutation already deferred |
| AccessChallengeResponse | `expires_at` has title only | none; mutation deferred |
| AccessLockdownResponse | `created_at` has title only | none; mutation deferred |
| AccessMeResponse | `session_expires_at` has title only | `get_me_api_v1_access_me_get` |
| AccessPaymentIntentResponse | `expires_at` anyOf includes empty schema | none; mutation deferred |
| AccessPaymentIntentStatusResponse | `expires_at` anyOf includes empty schema | `get_payment_intent_status_api_v1_access_payment_intents__payment_intent_id__get` |
| AccessSessionResponse | `expires_at` has title only | none; mutation deferred |
| ChildApiKeyCreateResponse | `expires_at` has title only | none; mutation deferred |
| ChildApiKeyPublic | `created_at`/`expires_at` have title-only schemas | `list_child_api_keys_api_v1_access_api_keys_get`, `get_child_api_key_api_v1_access_api_keys__key_id__get` |
| DelegatedPassCreateResponse | `expires_at` has title only | none; mutation deferred |
| DelegatedPassPublic | `valid_from`/`expires_at` have title-only schemas | `list_delegated_passes_api_v1_access_delegated_passes_get`, `get_delegated_pass_api_v1_access_delegated_passes__delegated_pass_id__get` |
| RecoveryStartResponse | `cooldown_until` has title only | none; mutation deferred |
| RecoveryStatusResponse | `cooldown_until` anyOf includes empty schema | `recovery_status_api_v1_access_recovery_status__recovery_attempt_id__get` |
| SubscriptionEntitlementResponse | `valid_from`/`valid_until`/`created_at` have title-only schemas | `get_my_entitlements_api_v1_access_me_entitlements_get` |
| ValidationError | `input` has title only | excluded from generated public errors by safe-error normalization; raw rejected input is forbidden |

The eight active operations consuming these source-deficient schemas are now individually `DEFERRED_WITH_REASON` under `P1B0-B03-SCHEMA`, with exact re-entry conditions. This is permitted source-contract deferment, not compiler-limitation deferment.

## Totals

| Measure | Result |
|---|---:|
| Active operations before source-schema deferment | 194 |
| Source-schema-deferred operations | 8 |
| Active operations after deferment | 186 |
| Previously selected generated bindings | 2 |
| Components | 286 |
| Compiler-normalized components | 271 |
| Source-contract failures | 15 |
| Component cycles | 0 |
| anyOf components | 76 total / 68 compiled / 8 source-blocked |
| additionalProperties components | 76 total / 68 compiled / 8 source-blocked |
| Full Python DTO modules emitted | 0 |
| Full callable operations emitted | 0 |
| Feature-53 full entries | 0 |

## Residual compiler stage

`SELECTED` no longer defines schema-normalization capability, but it still defines Python source emission in `scripts/generate_http_transport_foundation.py`. The normalized IR has not yet been rendered into deterministic Pydantic source for the remaining 186 operations, so full package generation, mypy, import-all, ownership, and Feature-53 completeness cannot pass.

## Smallest remediation

1. Backend Access owners replace the exact `Any` timestamp fields above with authoritative datetime schemas.
2. Implement a source renderer from `CompiledSchema` IR, emit the 186-operation package, then run mypy/import/idempotence and Feature-53 checks.

## Rollback

Remove the schema compiler, compiler tests, compiler preflight section, eight source-schema deferments, regenerated artifacts, and this report together. Rollback must return the eight operations to explicit blocked status, never infer types for backend `Any`, and never restore them as active generated ownership.
