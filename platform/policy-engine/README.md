# Policy engine

Owns centralized policy decisions, enforcement points, operator-governed rules and policy evaluation evidence.

Current canonical paths:

- `app/api/v1/policy.py`
- policy-oriented services under `app/services/`
- authorization/governance documentation under `docs/`

Migration rule: policy decisions must be explainable, auditable and safe to simulate before enforcement.
