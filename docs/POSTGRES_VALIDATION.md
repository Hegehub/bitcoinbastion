# PostgreSQL Staging Validation

## Required env
- `POSTGRES_TEST_DATABASE_URL` (required)
- `ALLOW_PRODLIKE_POSTGRES=1` only when intentionally targeting prod-like host/db name.

## Safety guarantees
- Scripts refuse to run without `POSTGRES_TEST_DATABASE_URL`.
- Scripts refuse prod-looking host/db names unless explicit override.
- No destructive downgrade is run against production-like DB unless override is explicitly set.

## Validation coverage
- Alembic upgrade to `head`.
- Migration replay (`upgrade -> downgrade base -> upgrade`) on isolated scratch DB.
- Schema parity checks: table parity, column parity, nullability, defaults, indexes, unique constraints, foreign keys.
- Accepted drift must be captured as explicit output in parity report.

## Commands
- `python scripts/run_postgres_migration_smoke.py`
- `python scripts/check_postgres_schema_parity.py`
