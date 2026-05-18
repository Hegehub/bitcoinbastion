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
