# PRODUCTION READINESS CHECKLIST

This checklist is a release-time gate for Bitcoin Bastion environments.

> Use this as an execution checklist per release/deploy cycle.
> Do not treat checked items as permanently true across future releases.

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
- [ ] Alembic head is current and migration chain validated.
- [ ] Migration reproducibility check passes (for current release branch).
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
- [ ] Unit and integration tests pass for modified scope.
- [ ] Contract tests pass for provider adapters touched by release.
- [ ] Release notes include operationally relevant changes.

## Operations
- [ ] Rollback plan documented.
- [ ] On-call runbook updated for new background jobs.
- [ ] Alert thresholds tuned for new metrics.
- [ ] Post-deploy verification steps documented.
