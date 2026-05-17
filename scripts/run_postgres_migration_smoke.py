#!/usr/bin/env python
from __future__ import annotations
import os, subprocess, tempfile
from urllib.parse import urlparse, urlunparse


def _url() -> str:
    u = os.environ.get("POSTGRES_TEST_DATABASE_URL", "").strip()
    if not u: raise SystemExit("POSTGRES_TEST_DATABASE_URL is required")
    if "prod" in u.lower() and os.environ.get("ALLOW_PRODLIKE_POSTGRES", "").lower() not in {"1","true","yes"}:
        raise SystemExit("Refusing prod-like DB URL")
    return u

def _clone_db_url(base: str, suffix: str) -> str:
    p = urlparse(base)
    db = (p.path or "/postgres").lstrip("/") + suffix
    return urlunparse((p.scheme,p.netloc,f"/{db}",p.params,p.query,p.fragment))

def _run(cmd: list[str], env: dict[str,str]) -> None:
    subprocess.run(cmd, check=True, env=env)

def main() -> int:
    base = _url()
    test_url = _clone_db_url(base, "_migration_smoke")
    env = os.environ.copy(); env["DATABASE_URL"] = test_url
    # create/drop isolated db through base connection
    import sqlalchemy as sa
    admin = sa.create_engine(base, isolation_level="AUTOCOMMIT", future=True)
    dbname = urlparse(test_url).path.lstrip("/")
    with admin.connect() as c:
        c.execute(sa.text(f'DROP DATABASE IF EXISTS "{dbname}"'))
        c.execute(sa.text(f'CREATE DATABASE "{dbname}"'))
    try:
        _run(["python","-m","alembic","upgrade","head"], env)
        _run(["python","-m","alembic","downgrade","base"], env)
        _run(["python","-m","alembic","upgrade","head"], env)
    finally:
        with admin.connect() as c:
            c.execute(sa.text(f'DROP DATABASE IF EXISTS "{dbname}"'))
    print("postgres migration smoke passed")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
