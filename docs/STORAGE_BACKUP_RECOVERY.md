# Storage Backup and Recovery

This document defines the current backup/restore evidence foundation for the Bitcoin Bastion Storage Layer. It does not claim production readiness, disaster-recovery readiness, or backup correctness by itself.

## Storage Evidence Artifacts

Storage evidence helpers can generate machine-readable JSON files under:

```text
artifacts/storage/
```

The directory is created only when evidence is written. Evidence files are deterministic JSON where practical, UTF-8 encoded, and accompanied by SHA-256 metadata returned by the writer.

Current evidence file names:

| Evidence file | Purpose |
| --- | --- |
| `storage_backup_evidence.json` | Records PostgreSQL backup hook readiness from supplied check results. |
| `storage_restore_evidence.json` | Records PostgreSQL restore/schema-parity/PITR hook readiness from supplied check results. |
| `redis_degraded_mode_evidence.json` | Records that Redis is treated as ephemeral degraded-mode infrastructure, not durable truth. |
| `object_storage_integrity_evidence.json` | Records Object Storage checksum/integrity evidence when object metadata is supplied. |
| `storage_outbox_replay_evidence.json` | Records durable outbox replay/idempotency evidence from supplied outbox check results. |
| `storage_health_evidence.json` | Records storage health status summaries for current and future engines. |

### What the artifacts prove

These artifacts prove only that a specific evidence generator received structured inputs and wrote a redacted JSON record at a point in time. They can document whether backup commands, restore commands, PITR strategy notes, schema parity hooks, object checksum comparisons, outbox replay counters, or storage health statuses were present in the supplied input.

### What the artifacts do not prove

These artifacts do not prove that:

- A real production backup succeeded.
- A real production restore succeeded.
- PostgreSQL PITR is operational.
- Object Storage retention/WORM controls are active.
- Redis is durable.
- TimescaleDB, ClickHouse, Qdrant, SQLite, or DuckDB are implemented.
- The platform is production-ready.

Unimplemented or missing infrastructure must be recorded as `skipped` or `not_configured`, not `pass`.

### Status meanings

Evidence checks use these statuses:

| Status | Meaning |
| --- | --- |
| `pass` | The supplied check result indicates success. |
| `warn` | The supplied check result is incomplete or degraded but not a hard failure. |
| `fail` | The supplied check result indicates a failed requirement or integrity mismatch. |
| `skipped` | The check was intentionally not automated or not executed. |
| `not_configured` | Required infrastructure or input was absent. |

### Secret policy

Evidence files must not contain:

- Seed phrases.
- Bitcoin private keys.
- Wallet files.
- `xprv`, `yprv`, or `zprv` material.
- Raw access tokens.
- Object Storage access keys or secret keys.
- Database passwords.
- Signed private URLs.
- Authorization headers or cookies.

The writer redacts sensitive keys and obvious sensitive values before writing JSON. Evidence should prefer hashes, fingerprints, object keys, counts, statuses, and non-secret operational metadata.

### Future work

Future prompts may wire these evidence helpers into CI jobs, operator runbooks, Object Storage artifact registration, release gates, and scheduled backup/restore validation jobs. Those integrations must continue to avoid fake readiness claims and must keep failed or skipped checks visible.
