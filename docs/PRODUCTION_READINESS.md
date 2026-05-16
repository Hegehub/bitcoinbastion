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
- [ ] Verify protocol source-quality labels are present for on-chain/citadel outputs (provider vs fallback vs mock).
- [ ] Verify fallback/synthetic protocol domains lower decision confidence in operational runbooks.
- [ ] Verify observability snapshot includes runtime severity, degraded mode, and operational evidence packet.
- [ ] Verify runtime metrics are exposed at `/metrics` for: severity score, degraded mode active, provider share, delivery failures, unresolved findings, citadel runtime health.
- [ ] Retry/timeout behavior verified for external integrations.
- [ ] Background job idempotency checks reviewed for touched tasks.
- [ ] Request IDs, logs, and metrics validated in deployed environment.
- [ ] Job execution telemetry available for operational triage.

## Recovery, drill, and SLO governance
- [ ] Recovery SLO status and unresolved critical findings are visible in `/api/v1/admin/jobs/recovery-check` and `/api/v1/observability/snapshot`.
- [ ] Drill posture (`next_drill_code`, `next_drill_priority`, `automated_drills_ready`) is reviewed weekly.
- [ ] Escalation thresholds are validated against environment-specific paging policies to reduce alert fatigue.
- [ ] Degraded mode and fallback semantics are acknowledged in release sign-off when active.

## Truth constraints
- Do not infer production SLO attainment from implemented endpoints.
- Treat **SYNTHETIC** and **BASELINE** components as non-final until explicitly hardened.
- Avoid percentage readiness claims in release documentation.

## Protocol maturity caveats
- Chain-state confidence is operational and conservative; it is not a consensus finality proof.
- Mempool/UTXO/script analytics are snapshot/hint-driven and must be treated as advisory unless corroborated by provider-grade evidence.
