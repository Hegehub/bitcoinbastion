# Bare-metal/systemd Runtime Notes

Bare-metal/systemd is an advanced fallback runtime profile for operators who do not want Docker Compose or Kubernetes. It preserves Bitcoin Bastion's no-custody posture: do not add seed phrase handling, private key handling, signing material, or wallet files.

## Operator responsibilities

- Provision PostgreSQL and Redis separately.
- Manage environment files and secrets outside Git.
- Run Alembic migrations intentionally before service start.
- Supervise API, worker, and beat processes with systemd units.
- Configure logs, metrics scraping, backups, restore drills, TLS, firewall rules, and rollback procedures.
- Collect deployment, migration, schema parity, provider health, backup/restore, and incident drill evidence before making production-readiness claims.

## Typical process commands

```bash
python -m alembic upgrade head
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
python -m celery -A app.tasks.celery_app.celery_app worker --loglevel=info
python -m celery -A app.tasks.celery_app.celery_app beat --loglevel=info
```

This profile has manual HA and manual evidence collection unless the operator adds external automation.
