# OpenAPI Stability

Bitcoin Bastion uses Proof-of-Access authorization for protected APIs. Legacy email/password authentication is disabled.

The legacy `/api/v1/auth/register` and `/api/v1/auth/login` operations remain only as deprecated compatibility stubs that return `legacy_auth_disabled`. They must not advertise password login as an active authentication flow or return bearer/JWT token schemas.

Access clients should use `/api/v1/access/*` endpoints and the Proof-of-Access headers documented in the OpenAPI security schemes.
