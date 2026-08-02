# Unified dependency migration

`app.api.access_dependencies` is the canonical authorization dependency layer.
Its immutable `UnifiedAccessContext` is also exported as `AccessContext` for
existing Access Layer routes. It performs PoP resolution, server-authoritative
context construction, revocation checks, entitlement checks, and Policy Engine
evaluation.

`app.api.wallet_auth_dependencies` is now a compatibility facade. Its legacy
resolver injection points remain for deployment composition and tests, while
its default behavior delegates to the canonical access context. New routes
must import canonical scope, metric, plan, business, PayRegister, offline, and
withdraw dependencies from `app.api.access_dependencies`.

Existing Access v1 routes may temporarily use `X-Bastion-*`. Wallet/LNURL v2
routes require `Authorization: PoP` and `Bastion-Request-*`. The legacy headers
must be removed after Python and TypeScript SDK migration (Prompts 67 and 68).
No Bearer compatibility exists for Wallet/LNURL v2.
