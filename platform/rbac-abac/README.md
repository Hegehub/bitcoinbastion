# RBAC/ABAC

Owns role-based and attribute-based authorization, permission modeling, access scopes and policy-bound enforcement.

Current canonical paths:

- `app/api/v1/policy.py`
- `app/services/access/`
- authorization checks in API/service code

Migration rule: authorization must be deny-by-default for privileged actions and observable through audit logs.
