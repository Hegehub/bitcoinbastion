# Deployment Evidence Pack

Use `python scripts/collect_release_evidence.py` to generate JSON release evidence into `artifacts/`.

## Required environment
- `POSTGRES_TEST_DATABASE_URL` for PostgreSQL smoke/parity checks.
- Optional: `ALLOW_PRODLIKE_POSTGRES=1` only for deliberate prod-like target testing.

## Exact commands
```bash
make docs-truthfulness
make migration-smoke
python scripts/collect_release_evidence.py --output artifacts/release_evidence.json
python scripts/run_postgres_migration_smoke.py --output-json artifacts/postgres_migration_smoke.json
python scripts/check_postgres_schema_parity.py --output-json artifacts/postgres_schema_parity.json
```

## Captured fields
- commit SHA
- timestamp
- environment
- lint/test/contract/regression results
- migration smoke result
- postgres schema parity result
- health/readiness result
- observability snapshot result
- recovery-check result
- metrics scrape result
- known limitations acknowledgement

## Notes
Some checks (observability snapshot, recovery-check, metrics scrape) require deployed runtime/API access; placeholders are recorded when unavailable.

## Attach to release
- Attach these artifacts to RC sign-off:
  - `artifacts/release_evidence.json`
  - `artifacts/postgres_migration_smoke.json`
  - `artifacts/postgres_schema_parity.json`
- Include pass/fail summary and any accepted drift justification in release notes.

## Kubernetes evidence capture workflow
Use Kubernetes jobs to generate the RC blocker artifacts in-cluster:

```bash
make k8s-run-migration
make k8s-run-postgres-migration-smoke
make k8s-run-postgres-schema-parity
make k8s-run-release-evidence
make k8s-collect-evidence-artifacts
```

Expected in-cluster output files:
- `/tmp/artifacts/release_evidence.json`
- `/tmp/artifacts/postgres_migration_smoke.json`
- `/tmp/artifacts/postgres_schema_parity.json`

## Sovereign runtime evidence extensions
Collect and attach additional evidence artifacts/logs from:
- `deploy/kubernetes/evidence/evidence-verify-job.yaml`
- `deploy/kubernetes/evidence/evidence-archive-job.yaml` (archive checksum)
- Drill executions (`provider-failure`, `recovery-slo`, `disaster-recovery`)
- Backup execution proof and staging restore-test proof

These extend (not replace) the core RC blocker artifacts.

- Evidence re-check CronJob is available: `deploy/kubernetes/evidence/evidence-recheck-cronjob.yaml`.

- Add burn-in, cutover, sign-off, backup verification, outage drill, and retention-policy evidence references from `deploy/kubernetes/operations/`.

- Attach observability validation job output plus active alert routing config and dashboard import evidence.

- Include GitOps promotion evidence: digest PR link, approval template, drift-check output, and evidence-gate checklist.

- Final RC certification references: `docs/KUBERNETES_RC_CERTIFICATION.md`, `docs/FINAL_KUBERNETES_READINESS_MATRIX.md`, `deploy/kubernetes/RC_EVIDENCE_CHECKLIST.md`.
