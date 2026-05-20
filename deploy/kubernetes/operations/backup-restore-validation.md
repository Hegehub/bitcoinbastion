# Backup/Restore validation
- Backup evidence: timestamp, db name, size/checksum if available, storage target, success/failure, retention class.
- Restore must be manual, default target is separate test DB.
- Production restore requires explicit operator confirmation.
- Validate backup exists, checksum (if present), restore success, app connectivity, schema parity, sample query.
- Document data-loss risks before executing production restore.
