# Production Readiness Checklist

This checklist is release-time evidence capture. Items must be verified per release.

## Label meanings
- **IMPLEMENTED**: capability exists in repository.
- **BASELINE**: capability exists but requires deeper operational validation.
- **SYNTHETIC**: placeholder behavior exists and must not be treated as production-grade.

## Release-candidate (RC) exit criteria
All criteria below must be met before promoting an RC to production:
- [ ] `make lint` passes.
- [ ] `python -m pytest -q tests/unit` passes.
- [ ] `python -m pytest -q tests/integration` passes.
- [ ] `python -m pytest -q tests/contract` passes.
- [ ] `python -m pytest -q tests/regression` passes.
- [ ] `make ci-release-gates` passes (migration replay + parity + docs truthfulness).
- [ ] Post-deploy verification commands (health, admin status, recovery check, observability snapshot, metrics) are captured with timestamps.
- [ ] Known BASELINE/SYNTHETIC limitations acknowledged in release sign-off.

## Final P6-10 decision guard
- Current repository-level sovereignty-grade readiness: **85%** (see `docs/STATUS.md`).
- **Do not claim 100% readiness** until all residual risks in `docs/STATUS.md` are explicitly closed with deployment evidence.
- RC promotion is allowed only as **conditional approval** pending environment verification evidence.

## Runtime and infrastructure
- [ ] Docker image build reproduced for release commit.
- [ ] Compose/runtime topology validated for API, DB, Redis, worker, beat.
- [ ] Health/readiness probes validated in target environment.
- [ ] Migration step executed and logged for deployment.
- [ ] Compose stack boot verified with health checks (`docker compose up -d --build` + service health status).
- [ ] Startup fails safely when required env/secrets are missing or insecure in production mode.
- [ ] Worker/beat startup ordering confirms Redis/Postgres readiness dependencies.

## Security and access
- [ ] Secrets sourced from environment/secret manager.
- [ ] JWT/admin guard behavior verified in staging.
- [ ] Audit-log generation verified for privileged actions.
- [ ] No-custody posture verified (no seed phrase/private-key handling paths in API/runtime).
- [ ] Admin RBAC guard verified for sensitive policy/treasury/admin endpoints (no silent bypass).

## Data and migrations
- [ ] Alembic head and migration chain verified on release commit.
- [ ] Migration reproducibility smoke passes (`make migration-smoke`).
- [ ] Schema parity checks pass (`python scripts/check_schema_runtime_parity.py`).
- [ ] Backward compatibility review completed for schema and API changes.
- [ ] Migration replay verified (`alembic upgrade head -> downgrade base -> upgrade head`) on a clean database artifact.
- [ ] Column/nullability/default/index/constraint parity checks reviewed (`python scripts/check_schema_runtime_parity.py`) and accepted drift (if any) documented.
- [ ] Rollback notes prepared for release migration set (expected downgrade path, data-loss caveats, operator decision points).
- [ ] Dialect-specific limitations acknowledged (SQLite parity is deterministic CI baseline; PostgreSQL semantics must be validated in staging for final sign-off).

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

## Known limitations (must be visible in every release sign-off)
- **BASELINE**: Telegram/delivery reliability is environment-dependent and requires deployment-specific validation.
- **BASELINE**: Mempool/UTXO/script analyzers are advisory and deterministic over provided snapshots/hints.
- **SYNTHETIC**: Parts of Citadel disaster and dependency simulation remain deterministic synthetic models.
- **Constraint**: Runtime confidence/finality values are operational heuristics, not consensus proofs.

## Protocol maturity caveats
- Chain-state confidence is operational and conservative; it is not a consensus finality proof.
- Mempool/UTXO/script analytics are snapshot/hint-driven and must be treated as advisory unless corroborated by provider-grade evidence.
