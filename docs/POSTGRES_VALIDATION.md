# PostgreSQL Staging Validation

## Required env
- `POSTGRES_TEST_DATABASE_URL` (required)
- `ALLOW_PRODLIKE_POSTGRES=1` only when intentionally targeting prod-like host/db name.

## Exact commands
```bash
python scripts/run_postgres_migration_smoke.py --output-json artifacts/postgres_migration_smoke.json
python scripts/check_postgres_schema_parity.py --output-json artifacts/postgres_schema_parity.json
```

## Safety guarantees
- Scripts refuse to run without `POSTGRES_TEST_DATABASE_URL`.
- Scripts refuse prod-looking host/db names unless explicit override.
- No destructive downgrade is run against production-like DB unless override is explicitly set.
- Migration smoke uses a scratch cloned database name (`<base_db>_migration_smoke`) and drops only that scratch DB.

## Validation coverage
- Alembic upgrade to `head`.
- Migration replay (`upgrade -> downgrade base -> upgrade`) on isolated scratch DB.
- Schema parity checks: table parity, column parity, nullability, defaults, indexes, unique constraints, foreign keys.
- Accepted drift must be captured as explicit output in parity report.

## Pass / fail criteria
- **PASS**: migration smoke returns `ok: true` and schema parity returns `ok: true`.
- **FAIL**: any check returns non-zero or parity `error_count > 0`.

## Accepted drift policy
- Any accepted drift must be explicitly documented in release notes and attached evidence JSON; silent drift is not accepted.

## Commands
- `python scripts/run_postgres_migration_smoke.py`
- `python scripts/check_postgres_schema_parity.py`

## Kubernetes job option
For target-environment validation, run:

```bash
make k8s-run-postgres-migration-smoke
make k8s-run-postgres-schema-parity
```

Then export artifacts from job pods into local `artifacts/` for release evidence attachment.
