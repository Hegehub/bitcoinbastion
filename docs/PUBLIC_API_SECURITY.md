# Public API Security

Bitcoin Bastion uses Proof-of-Access authorization for protected APIs. Legacy email/password authentication is disabled.

Public status and marketing-safe endpoints may remain unauthenticated. Protected endpoints must require Proof-of-Access dependencies, request-signature verification where required, revocation checks, and an Access Policy Engine decision.

Bastion never asks for a Bitcoin seed, Bitcoin private key, recovery phrase, raw Access Pass as bearer proof, password, or mandatory email address for protected API authentication.
