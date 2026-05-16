# Security Posture (No-Custody)

Audit date: **2026-05-16**

## Non-negotiable custody constraints
- The service is **no-custody by design**.
- Seed phrases are not accepted, stored, derived, or transmitted by runtime APIs.
- Private keys are not accepted, stored, derived, or transmitted by runtime APIs.
- Treasury and policy workflows are governance/evaluation layers; they do not perform key management.

## Secrets and JWT controls
- `JWT_SECRET_KEY` must be strong in production (non-default and minimum length enforced).
- JWT verification requires `sub`, `exp`, `iat`, and `iss` claims.
- JWT issuer is explicitly validated via `JWT_ISSUER`.
- `JWT_ALGORITHM` is constrained to `HS256` in production unless explicit cryptographic review is performed.

## Admin and RBAC guardrails
- Admin-only route access requires both:
  - `is_admin == true`
  - `role == "admin"`
- Sensitive policy and treasury actions require admin authentication.
- No silent bypass path is accepted for admin-only operations.

## Sensitive action auditability
- Treasury create/approve/reject actions are audit-logged with actor and status transitions.
- Policy high-risk changes require explicit governance metadata (justification/ticket/peer approvals).

## Dangerous input handling
- Security-sensitive payload fields are length constrained at schema boundaries.
- Policy and treasury actions are validated through typed schema models and explicit ranges.

## Accepted limitations
- CI/schema checks use SQLite for deterministic parity/replay evidence.
- PostgreSQL-specific semantics still require staged environment verification before production sign-off.


## P7-02 verification snapshot (2026-05-16)
- **No seed phrase storage found** in `app/` or `tests/` paths scanned for mnemonic/seed phrase patterns.
- **No private key storage found** in API/service/model paths scanned for private key/xprv/wif markers.
- **No accidental key logging evidence found** in runtime code scan for direct sensitive token/secret logging patterns.
- **Admin routes protected** by `get_admin_user` dependency and dual admin checks (`is_admin` + `role=admin`).
- **Sensitive treasury actions audited** via `treasury.request.create|approve|reject` audit events.
- **Policy sensitive actions audited/governed** through policy execution logging and high-risk change controls.
- **Env handling safe by design** with production guardrails for JWT secret/issuer/algorithm and fail-fast startup checks.
- **Debug production posture**: no `debug=True` runtime mode found in API startup path.

### Findings classification
- **BLOCKER:** none found in repository-level static/runtime test verification.
- **MAJOR:** none found in this verification pass.
- **MINOR:** deployment environment secret hygiene still requires operator evidence per release checklist.
