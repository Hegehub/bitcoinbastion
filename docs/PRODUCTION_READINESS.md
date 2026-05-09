# Production Readiness Checklist

This checklist is release-time evidence capture. Items must be verified per release.

## Label meanings
- **IMPLEMENTED**: capability exists in repository.
- **BASELINE**: capability exists but requires deeper operational validation.
- **SYNTHETIC**: placeholder behavior exists and must not be treated as production-grade.

## Runtime and infrastructure
- [ ] Docker image build reproduced for release commit.
- [ ] Compose/runtime topology validated for API, DB, Redis, worker, beat.
- [ ] Health/readiness probes validated in target environment.
- [ ] Migration step executed and logged for deployment.

## Security and access
- [ ] Secrets sourced from environment/secret manager.
- [ ] JWT/admin guard behavior verified in staging.
- [ ] Audit-log generation verified for privileged actions.

## Data and migrations
- [ ] Alembic head and migration chain verified on release commit.
- [ ] Migration reproducibility smoke passes (`make migration-smoke`).
- [ ] Schema parity checks pass (`python scripts/check_schema_runtime_parity.py`).
- [ ] Backward compatibility review completed for schema and API changes.

## Reliability and observability
- [ ] Retry/timeout behavior verified for external integrations.
- [ ] Background job idempotency checks reviewed for touched tasks.
- [ ] Request IDs, logs, and metrics validated in deployed environment.
- [ ] Job execution telemetry available for operational triage.

## Truth constraints
- Do not infer production SLO attainment from implemented endpoints.
- Treat **SYNTHETIC** and **BASELINE** components as non-final until explicitly hardened.
- Avoid percentage readiness claims in release documentation.
