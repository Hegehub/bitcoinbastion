# Auth

Owns authentication, identity, session/access boundaries, user flows and Proof-of-Access integration points.

Current canonical paths:

- `app/api/v1/auth.py`
- `app/api/v1/users.py`
- `app/services/access/`

Migration rule: auth changes must preserve no-custody boundaries and must never request, store or transmit wallet seed/private-key material.
