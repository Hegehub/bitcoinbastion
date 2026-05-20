# Release Notes Template

## Release metadata
- Version candidate: `v0.1.0-rc.1`
- Release date (UTC): `<YYYY-MM-DD>`
- Release manager: `<name>`
- Commit SHA: `<sha>`
- Scope: Sovereignty-grade RC governance, security hardening, API contract lock, deployment/runbook readiness

## Release candidate criteria (must be explicitly checked)
- [ ] `make lint`
- [ ] `python -m pytest -q tests/unit`
- [ ] `python -m pytest -q tests/integration`
- [ ] `python -m pytest -q tests/contract`
- [ ] `python -m pytest -q tests/regression`
- [ ] `make ci-release-gates`
- [ ] Deploy verification commands executed and attached.
- [ ] Known BASELINE/SYNTHETIC limitations acknowledged.

## Summary
- What changed and why.

## API and contracts
- New endpoints / schema changes / backward compatibility notes.

## Data and migrations
- Migration ids affected.
- Rollback and compatibility notes.

## Operational impact
- Background jobs affected.
- Alert thresholds affected.
- Runbook updates required.

## Verification
- Test commands executed.
- Post-deploy checks executed.

### Exact verification commands executed
```bash
make lint
python -m pytest -q tests/unit
python -m pytest -q tests/integration
python -m pytest -q tests/contract
python -m pytest -q tests/regression
make ci-release-gates

curl -fsS http://localhost:8000/api/v1/health/live
curl -fsS http://localhost:8000/api/v1/health/ready
curl -fsS -H "Authorization: Bearer <ADMIN_TOKEN>" http://localhost:8000/api/v1/admin/status
curl -fsS -H "Authorization: Bearer <ADMIN_TOKEN>" http://localhost:8000/api/v1/admin/jobs/recovery-check
curl -fsS -H "Authorization: Bearer <ADMIN_TOKEN>" http://localhost:8000/api/v1/observability/snapshot
curl -fsS http://localhost:8000/metrics
```

## Risks and mitigations
- Known risks.
- Mitigation plan and owner.

## Rollback notes
- Rollback trigger observed:
- Previous image digest/version:
- Rollback executed by:
- Migration compatibility checks run:
- Post-rollback verification commands run:


## Upgrade notes
- Apply migrations to head before switching traffic: `python -m alembic upgrade head`.
- Ensure env includes `JWT_ISSUER` and `JWT_ACCESS_TOKEN_EXPIRES_MINUTES` and uses strong non-default `JWT_SECRET_KEY` for production.
- For container deployment, use startup scripts that enforce env guards and migration-at-start behavior.
- Validate admin token flow after deploy because JWT issuer/claim enforcement is strict (`sub`, `exp`, `iat`, `iss`).

## Migration notes
- Migration replay expectation: `upgrade head -> downgrade base -> upgrade head` remains reproducible on clean artifact.
- Schema parity/model-migration parity checks are mandatory RC gates.
- SQLite parity is deterministic CI baseline; PostgreSQL semantics must be verified in staging before production promotion.

## Known limitations (explicit)
- Protocol confidence remains advisory (not consensus/finality proof).
- Citadel includes deterministic synthetic simulation components.
- Telegram/delivery behavior remains environment-dependent.
- Deployment evidence capture remains operator-driven per release checklist.


## RC decision field (required)
- Decision class: `PRODUCTION RELEASE CANDIDATE` / `RC-ready pending environment evidence` / `PRE-RC / PRODUCTION-ORIENTED BETA` / `NOT READY`
- Final audit reference: `docs/FINAL_PRODUCTION_GAP_AUDIT.md`

## Evidence attachment field (required for RC promotion)
- [ ] `artifacts/release_evidence.json` attached
- [ ] `artifacts/postgres_migration_smoke.json` attached
- [ ] `artifacts/postgres_schema_parity.json` attached

## GitOps Promotion Metadata
- Environment path promoted from/to:
- Image digest promoted:
- Evidence gate checklist reference:
- Production approval reference:
- Rollback commit reference:

## Kubernetes RC Certification References
- KUBERNETES_RC_CERTIFICATION.md reviewed: 
- FINAL_KUBERNETES_READINESS_MATRIX.md reviewed: 
- OPERATOR_RUNBOOK_LOCK accepted: 
