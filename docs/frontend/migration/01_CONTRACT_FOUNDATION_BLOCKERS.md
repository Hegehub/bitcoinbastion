# Stage-1 Contract Blocker Register

The canonical HTTP generation blockers are **RESOLVED** for the current authoritative
HTTP set. The generated source, ownership registry, Feature-53 registry, manifest and
validators are owned by `scripts/generate_http_transport.py`.

| Blocker | State | Evidence / remaining condition |
|---|---|---|
| P1B0-B01 security projection | RESOLVED | Active protected bindings carry an Access security identity and exclude Bastion security headers from ordinary request DTOs. |
| P1B0-B02 mutation authority | RESOLVED | No unresolved mutation is in the active generation set; deferred mutations retain blocker/owner/re-entry metadata. |
| P1B0-B03 schema/emission | RESOLVED | 286 schemas and 194 operations generate, import, typecheck and resolve exactly one owner/Feature-53 entry. |
| P1R2-B05 | DEFERRED_TO_PROMPT_4 | WebSocket wire-version authority unavailable. |
| P1R2-B06 | DEFERRED_TO_PROMPT_4 | WebSocket wire-version authority unavailable. |
| P1R2-B07 | DEFERRED_TO_PROMPT_4 | WebSocket wire-version authority unavailable. |
| P1R2-B08 | DEFERRED_TO_PROMPT_4 | WebSocket wire-version authority unavailable. |
| P1R2-B09 | DEFERRED_TO_PROMPT_4 | WebSocket wire-version authority unavailable. |
| P1R2-B10 | DEFERRED_TO_PROMPT_4 | WebSocket wire-version authority unavailable. |
| P1R2-B11 | DEFERRED_TO_PROMPT_4 | WebSocket wire-version authority unavailable. |
| P1R2-B12 | DEFERRED_TO_PROMPT_4 | WebSocket wire-version authority unavailable. |
| P1R2-B13 | DEFERRED_TO_PROMPT_4 | WebSocket wire-version authority unavailable. |

Deferred WebSocket entries are registry facts only. Prompts 2 and 3 must not open or
consume them. Prompt 4 must establish version, compatibility and message authority
before implementing lifecycle behavior.

## Prompt-2 input contract

Prompt 2 consumes:

`generated transport DTO -> domain adapter -> safe view model -> Reflex State -> component`.

Prompt 2 must not bypass generated callables, parse a raw response dictionary when a
generated DTO exists, recalculate backend conclusions, or consume a deferred WebSocket
family. Stage-1 `CLIENT_ONLY` is transport evidence, not render evidence.

## Rollback

Revert generated schemas, generated HTTP bindings, manifest, ownership/Feature-53
registries and revision-bound matrices together. A rollback must restore the preceding
blocked state; it must not reactivate legacy auth, assign a deferred operation an owner,
or invent WebSocket authority.
