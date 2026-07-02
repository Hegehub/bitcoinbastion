# Security

Owns hardening, threat model, secure defaults, abuse controls, supply-chain checks and security review evidence.

Current canonical paths:

- `app/api/middleware.py`
- security documentation under `docs/`
- CI security checks where present

Migration rule: security-sensitive changes must include explicit assumptions, failure modes and rollback guidance.
