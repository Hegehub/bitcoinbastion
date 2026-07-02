# Admin panel

Owns protected operator/admin interfaces, support workflows, privileged actions and administrative safety rails.

Current canonical paths:

- `app/api/v1/admin.py`
- admin/operator views under `app/web/`

Migration rule: admin workflows must require explicit authorization, auditability and clear degraded-state behavior.
