# Public API

Public APIs are presentation-safe abstractions under `/api/v1/public/*`.

- Advisory-only responses.
- No seed/private key acceptance.
- No internal evidence chains exposed by default.
- No transaction authorization/signing.


OpenAPI stability baseline documented in `docs/OPENAPI_STABILITY.md`. Public-safe schemas must not expose private keys, seed data, provider credentials, operator-only notes, raw audit chains, or internal topology.
