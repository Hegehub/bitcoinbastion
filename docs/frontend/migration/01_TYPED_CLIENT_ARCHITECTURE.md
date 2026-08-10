# Stage-1 HTTP Typed-Client Architecture

## Decision

Use **generated typed operation descriptors over one shared injectable transport engine**.

The generator reads runtime OpenAPI plus the deterministic disposition/authority matrix. It emits one descriptor owner per `AUTHORITATIVE_NOW` HTTP operation with an active UI disposition. Deferred and non-UI operations receive no generic client owner. PayRegister remains outside the Core generation set and requires its separate product transport module.

Prompt 1A generates `01_HTTP_CLIENT_OWNERSHIP_INPUT.json` as an architecture input, not proof that clients exist. Prompt 1B pre-flight found that all 309 candidates still use a generic unverified error description and unreviewed security metadata. They therefore remain blocked candidates with no owner until strict Python request/response/error bindings and reviewed security metadata are generated. Prompt 2 alone owns domain adapters and view models.

## Alternatives

* Operation-specific handwritten methods were rejected because hundreds of wrappers would duplicate OpenAPI metadata and drift.
* Fully generated domain modules were rejected because transport generation must not imply domain ownership or pull Prompt-2 adapters forward.
* A generic untyped dispatcher was rejected because it would make raw dictionaries canonical and could expose deferred or non-UI routes.
* A hybrid remains permitted only for media/stream cases that the descriptor engine cannot represent, with a documented exception and exactly-one-owner invariant.

## Security and products

Descriptors carry requirements, never secrets. Approved signing/session providers must be injected through narrow interfaces; generated code must not persist device keys, PoP material, nonces, recovery factors, payment proofs, bearer tokens, or Bitcoin secrets. Unsafe mutations are never blindly retried. Callback, protocol, backend-only, and deferred operations are excluded. PayRegister stays separately generated and separately navigated.

## Rollback

Revert the ownership input and generator changes together. Deferred operations must remain deferred after rollback; do not restore generic ownership or fabricate WebSocket versions.
