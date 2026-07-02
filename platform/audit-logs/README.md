# Audit logs

Owns immutable operator/security audit records, audit event taxonomy, audit exports and evidence trails for privileged activity.

Current canonical paths:

- audit-producing services under `app/services/`
- audit/evidence documentation under `docs/`

Migration rule: audit logs must be tamper-evident where possible, append-oriented and separate from ordinary debug logs.
