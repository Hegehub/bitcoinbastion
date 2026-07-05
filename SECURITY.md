# Security

Report vulnerabilities privately to maintainers.

Current posture:
- security hardening baseline implemented
- production security validation pending

Do not commit secrets, credentials, or private operational data.
No fake security claims (e.g., "fully secure" or pentest-complete) without evidence.

## Proof-of-Access authentication

Bitcoin Bastion uses Proof-of-Access authorization for protected APIs. Legacy email/password authentication is disabled. Bastion will never ask for your Bitcoin seed or Bitcoin private key.
