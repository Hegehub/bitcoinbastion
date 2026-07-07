# OpenAPI Stability

Bitcoin Bastion uses Proof-of-Access authorization for protected APIs. Legacy email/password authentication is disabled.

The legacy `/api/v1/auth/register` and `/api/v1/auth/login` operations remain only as deprecated compatibility stubs that return `legacy_auth_disabled`. They must not advertise password login as an active authentication flow or return bearer/JWT token schemas.

Access clients should use `/api/v1/access/*` endpoints and the Proof-of-Access headers documented in the OpenAPI security schemes.

## Proof-of-Access endpoint security annotations

OpenAPI includes Proof-of-Access security schemes for `X-Bastion-Session`, per-request `X-Bastion-Signature`, and `X-Bastion-Intent-Signature`. Protected operations are annotated with `x-proof-of-access-required` and must not advertise password/JWT as active auth for premium endpoints.

## Access contract stability

The Access API contract treats plan codes, scope names, metric names, request-signing headers, and structured error codes as stable public contracts. Changes to `X-Bastion-Session`, `X-Bastion-Timestamp`, `X-Bastion-Nonce`, `X-Bastion-Body-Hash`, `X-Bastion-Signature`, and `X-Bastion-Intent-Signature` require explicit migration notes.

OpenAPI must not present password login as the main auth path. Deprecated legacy auth stubs may remain visible only when marked disabled/deprecated and returning `legacy_auth_disabled`. Access Pass must never be described as a bearer token.

Current OpenAPI limitations: OpenAPI can declare the required header security schemes and endpoint descriptions, but it cannot fully express canonical digest construction, nonce replay storage, or device-key verification. Those semantics are normative in `docs/ACCESS_REQUEST_SIGNING.md`.
