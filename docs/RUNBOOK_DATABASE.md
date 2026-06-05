# Runbook: Database Restore

## Signals
- `/health/dependencies` reports `database` as degraded or critical.
- `BitcoinBastionDatabaseUnavailable` alert fires.
- `GET /api/v1/operations/status` shows degraded_state and operational_limitations.

## Actions
1. Freeze publishing and operator approvals if migrations or integrity are uncertain.
2. Confirm latest backup and PITR window.
3. Restore into staging first, run migration smoke, then promote through GitOps.
4. Record an `operations_evidence` row with drill type `database_restore` and artifact references.

## Evidence
Attach backup ID, migration revision, smoke-test output and operator sign-off.
