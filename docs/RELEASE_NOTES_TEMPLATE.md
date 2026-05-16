# Release Notes Template

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
