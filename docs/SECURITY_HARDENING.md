# Security Hardening

Security hardening baseline implemented.
HTTP security headers and CSP baseline are applied by middleware.
Rate limiting is baseline and should also exist at infrastructure level.
CSP and headers may require production tuning.
Production penetration testing is not yet completed.

## Proof-of-Access hardening

Legacy password/JWT auth is disabled for protected access. Production deployments must protect Access issuer keys, server pepper, BTCPay secrets, recovery material, and session/signature telemetry. Do not log raw Access Passes, session tokens, recovery phrases, signatures, private keys, or Bitcoin seed material.
