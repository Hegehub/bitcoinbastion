# Disaster Recovery

Status: **ACTIVE BASELINE / PRODUCTION DRILL EVIDENCE PENDING**.

Bitcoin Bastion recovery is deterministic: backup verification, restore verification, replay validation and integrity checks must succeed before readiness can be claimed.

## Capabilities

- backup verification
- restore verification
- timeline rebuild
- candle rebuild
- event rebuild
- evidence rebuild
- signal rebuild
- integrity validation

Backup validation records `backup_id`, timestamps, success, objects checked, integrity status and limitations. Recovery validation replays news events, candles, impacts, attributions, signals and evidence and records whether deterministic rebuild was verified.

The presence of backup, restore, and replay code does not prove recovery
readiness. Timed restore drills, environment-specific RPO/RTO evidence, and
operator sign-off remain required. Storage-specific procedures and evidence
requirements are defined in [STORAGE_BACKUP_RECOVERY.md](STORAGE_BACKUP_RECOVERY.md).
