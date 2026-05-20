# Backup & restore

- Backup schedule: daily at 02:00 cluster time (adjust per policy).
- Restore job is manual/explicit and requires operator confirmation env.
- No credentials are hardcoded.
- Test restore in staging before production and document rollback/data retention caveats.

- `backup-verification-job.yaml` provides evidence-friendly verification logging for backups.
