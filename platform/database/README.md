# Database

Owns relational persistence, SQLAlchemy models, Alembic migrations, schema parity checks and migration smoke evidence.

Current canonical paths:

- `app/models/`
- `alembic/`
- database-related tests under `tests/`

Migration rule: every schema change must include migration, downgrade/rollback reasoning and test evidence.
