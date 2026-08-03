# Data Contract and Provenance Matrix

| Layer | Owner | Required contract | Prohibited shortcut |
|---|---|---|---|
| OpenAPI/WS | FastAPI routers and schemas | revision-pinned normalized contract, unique IDs, security extensions | copied docs or hand-written URL truth |
| Transport | generated/typed frontend client | typed request/response/error, timeout/cancellation, exact URL | raw dict preview |
| Domain adapter | screen domain | normalization, units, optionality, conflict/stale computation | policy/business calculations in component |
| View-model/State | route owner | provenance, freshness, privacy class and complete UI state union | “loaded” boolean only |
| Component | domain component | named fields, semantic table/text alternative, safe copy/share | placeholder/static JSON |

Every rendered model includes `source_revision`, `observed_at`, `freshness`, and one provenance state: **LIVE**, **VERIFIED_SNAPSHOT**, **DEMO_FIXTURE**, or **UNAVAILABLE**. Synthetic and fixtures are never visually indistinguishable from live data. Conflicting sources remain a first-class state rather than being averaged away in the UI.

Privacy classes are `PUBLIC_SHAREABLE`, `PUBLIC_NO_INDEX`, `OPERATOR_RESTRICTED`, `SESSION_EPHEMERAL`, and `ONE_TIME_SECRET`. Only fields explicitly classified `PUBLIC_SHAREABLE` may enter deep links or sharing; persistence and clipboard each need separate approval.
