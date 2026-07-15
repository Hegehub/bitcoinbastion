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
curl -fsS \
  -H "X-Bastion-Session: <POP_SESSION>" \
  -H "X-Bastion-Timestamp: <ISO8601>" \
  -H "X-Bastion-Nonce: <NONCE>" \
  -H "X-Bastion-Body-Hash: <SHA256_EMPTY_BODY>" \
  -H "X-Bastion-Signature: <DEVICE_SIGNATURE>" \
  http://localhost:8000/api/v1/admin/status
curl -fsS \
  -H "X-Bastion-Session: <POP_SESSION>" \
  -H "X-Bastion-Timestamp: <ISO8601>" \
  -H "X-Bastion-Nonce: <NONCE>" \
  -H "X-Bastion-Body-Hash: <SHA256_EMPTY_BODY>" \
  -H "X-Bastion-Signature: <DEVICE_SIGNATURE>" \
  http://localhost:8000/api/v1/observability/snapshot
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
- Ensure Access Layer env is configured: `ACCESS_SERVER_PEPPER`, `ACCESS_ISSUER_KEY_ID`, `ACCESS_ISSUER_PRIVATE_KEY`, session/challenge TTLs, and payment provider settings.
- `JWT_*` settings are legacy-disabled and must not be used for protected API access.
- For container deployment, use startup scripts that enforce env guards and migration-at-start behavior.
- Validate Proof-of-Access admin flow after deploy with `X-Bastion-*` request signing headers.

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
- Current status reference: `docs/STATUS.md`
- Revision/environment evidence reference: `<artifact or archived audit path>`

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
