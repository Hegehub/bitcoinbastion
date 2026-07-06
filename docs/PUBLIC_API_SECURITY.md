# Public API Security

Bitcoin Bastion uses Proof‑of‑Access authorization for all protected APIs. Legacy email/password authentication is disabled.

## Public versus premium boundaries

Public endpoints (health, status, marketing materials, lite trace endpoints, etc.) remain unauthenticated and do not require Proof‑of‑Access. They return only liveness information, version identifiers or intentionally public data and must not expose sensitive operational or subscription data.

Premium or private endpoints require a valid Proof‑of‑Access session (`X‑Bastion‑Session`) and per‑request signature headers (`X‑Bastion‑Timestamp`, `X‑Bastion‑Nonce`, `X‑Bastion‑Body‑Hash`, `X‑Bastion‑Signature`). Without a valid session and signature the server returns structured error responses such as `invalid_session`, `invalid_request_signature`, `timestamp_stale` or `nonce_reused` rather than leaking data.

## Error responses and plan upgrades

Access denial uses structured JSON with a stable `code` and human‑readable `message`. Lower‑tier plans receive `plan_upgrade_required`, `scope_not_allowed` or `metric_not_allowed` when requesting endpoints or metrics that are not included in their plan. The API must never return partial data that leaks subscription entitlements, certificate internals or policy decisions to unauthenticated clients.

Providers and integration clients should enforce plan checks and scope enforcement on the client side as well. Premium endpoints may also return `certificate_revoked`, `session_revoked`, `certificate_not_found` or `entitlement_expired` according to the recovery, revocation and policy rules.

## Safety guarantees

Bastion will never ask for your Bitcoin seed, Bitcoin private key, raw Access Pass as bearer proof, password or mandatory email address. Proof‑of‑Access sessions are bound to a device key and origin and require per‑request signatures. Session tokens alone are not sufficient for protected access.

Endpoints that remain public must not expose internal state, server secrets, policy decisions or entitlement details. Operators should audit new endpoints for appropriate Proof‑of‑Access requirements and classification as public or premium.
