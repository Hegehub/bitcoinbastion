# PRODUCTION READINESS CHECKLIST

This checklist is the deployment baseline for Bitcoin Bastion environments.

## Runtime and infrastructure
- [ ] Docker image builds reproducibly.
- [ ] `docker-compose` stack includes app, db, redis, worker, beat.
- [ ] Health endpoints are wired to orchestration probes.
- [ ] Database migrations are applied at startup/deploy stage.

## Security and access
- [ ] Secrets loaded from environment only.
- [ ] JWT secrets meet production entropy requirements.
- [ ] Auth and admin guards enforced for privileged endpoints.
- [ ] Sensitive actions emit audit logs.

## Data and schema safety
- [x] Alembic head is current and migration chain validated (CI `migration-smoke` job).
- [x] Migration reproducibility check passes (CI runs `scripts/check_alembic_reproducibility.sh`).
- [ ] Backward compatibility assessed for schema/API changes.

## Reliability
- [ ] External integrations have timeouts and retry strategy.
- [ ] Background jobs are idempotent where practical.
- [ ] Duplicate suppression exists for delivery/signals where needed.
- [ ] Provider outages degrade gracefully with visibility.

## Observability
- [ ] Structured JSON logging enabled.
- [ ] Request ID propagation enabled.
- [ ] Prometheus metrics exposed and scrapeable.
- [ ] Job execution telemetry recorded.
- [ ] Readiness endpoint validates critical dependencies.

## Quality gates
- [ ] Lint + format checks pass.
- [x] Unit and integration tests pass for modified scope (validated in CI/local runs).
- [x] Contract tests pass for provider adapters touched by release (CI `contracts` job).
- [x] Release notes include operationally relevant changes (`docs/RELEASE_NOTES_TEMPLATE.md`).

## Operations
- [x] Rollback plan documented (`docs/OPERATIONS_RUNBOOK.md`).
- [x] On-call runbook updated for new background jobs (`docs/OPERATIONS_RUNBOOK.md`).
- [x] Alert thresholds tuned for new metrics (`docs/ALERT_THRESHOLDS.md`).
- [x] Post-deploy verification steps documented (`docs/OPERATIONS_RUNBOOK.md`).
