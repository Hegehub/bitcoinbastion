# Runbooks

Operational runbooks live under `docs/runbooks/`:

- provider failure
- timeline rebuild
- evidence integrity
- signal queue recovery
- Telegram failure
- database restore
- full disaster recovery

Every runbook preserves the safety rule: degraded state, backup verification, restore verification, integrity verification and operator visibility must be explicit.
