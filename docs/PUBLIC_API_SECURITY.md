# Public API Security

Bitcoin Bastion uses Proof-of-Access authorization for protected APIs. Legacy email/password authentication is disabled.

Public status and marketing-safe endpoints may remain unauthenticated. Protected endpoints must require Proof-of-Access dependencies, request-signature verification where required, revocation checks, and an Access Policy Engine decision.

Bastion never asks for a Bitcoin seed, Bitcoin private key, recovery phrase, raw Access Pass as bearer proof, password, or mandatory email address for protected API authentication.

## Public versus premium boundaries

Public endpoints are limited to health/liveness, public landing/status, intentionally public trace-lite/address checks, public docs, and other non-sensitive read-only surfaces. Provider/internal health, operations dashboards, treasury, policy management, business trace, enterprise trace, webhook management, metrics usage, admin/operator, and developer-management endpoints require Proof-of-Access.
