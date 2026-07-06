# OpenAPI Stability

The Bitcoin Bastion OpenAPI contract reflects the Proof‑of‑Access model and stability promises. No legacy password-based login flows are part of the stable contract.

## Deprecated legacy endpoints

The `/api/v1/auth/register` and `/api/v1/auth/login` operations remain only as deprecated compatibility stubs that return `legacy_auth_disabled`. They must not advertise password login, return bearer/JWT token schemas, or accept email/password credentials. These endpoints may be removed in a future major version.

## Proof‑of‑Access security schemes

The OpenAPI specification defines named security schemes for `BastionProofOfAccessSession`, `BastionProofOfAccessSignature` and `BastionHumanIntentSignature`. Protected operations include these schemes in their `security` array and set an `x-proof-of-access-required` boolean. Clients must send `X‑Bastion‑Session` and `X‑Bastion‑Signature` headers and sign requests as described in `docs/ACCESS_REQUEST_SIGNING.md`.

While `X‑Bastion‑Timestamp`, `X‑Bastion‑Nonce` and `X‑Bastion‑Body‑Hash` are not modelled as separate security schemes, they are documented at the endpoint level and required by all premium operations.

## Contract stability rules

- **No password login**: The contract must never reintroduce mandatory email/password login or bearer tokens as a valid auth method.
- **Header names**: The `X‑Bastion‑*` headers for Proof‑of‑Access sessions, request signatures, timestamps and nonces are stable. Changes to these header names would constitute a breaking change.
- **Error codes**: Standard error code strings (e.g. `unpaid_payment_intent`, `invalid_challenge`, `nonce_reused`, `timestamp_stale`, `plan_upgrade_required`) are part of the contract. Additional error codes may be added but existing codes must not change meaning.
- **Plans and scopes**: Plan codes (`lite_pass`, `basic_pass`, `plus_pass`, `pro_pass`, `business_pass`, `enterprise_pass`) and scope names remain stable across versions. New plans/scopes may be introduced but existing ones must not change semantics.
- **Request/response shapes**: Fields and nested properties defined in the OpenAPI contract must remain consistent with the documented behaviour. Optional fields may be added with defaults that do not break existing clients.

## Known limitations of the OpenAPI model

FastAPI/OpenAPI cannot fully express the dynamic nature of Proof‑of‑Access request signing. It models the `X‑Bastion‑Session` and `X‑Bastion‑Signature` headers but cannot enforce timestamp freshness, nonce uniqueness or body hash verification. These checks are documented in `docs/ACCESS_REQUEST_SIGNING.md` and validated at runtime.
