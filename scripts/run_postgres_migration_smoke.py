#!/usr/bin/env python
from __future__ import annotations
import argparse
import json
import os
import subprocess
from urllib.parse import urlparse, urlunparse


def _url(*, allow_prodlike: bool) -> str:
    u = os.environ.get("POSTGRES_TEST_DATABASE_URL", "").strip()
    if not u:
        raise SystemExit("POSTGRES_TEST_DATABASE_URL is required")
    if "prod" in u.lower() and not allow_prodlike:
        raise SystemExit("Refusing prod-like DB URL")
    return u


def _clone_db_url(base: str, suffix: str) -> str:
    p = urlparse(base)
    db = (p.path or "/postgres").lstrip("/") + suffix
    return urlunparse((p.scheme, p.netloc, f"/{db}", p.params, p.query, p.fragment))


def _run(cmd: list[str], env: dict[str, str]) -> None:
    subprocess.run(cmd, check=True, env=env)


def _run_capture(cmd: list[str], env: dict[str, str]) -> dict[str, object]:
    proc = subprocess.run(cmd, text=True, capture_output=True, env=env)
    return {
        "cmd": " ".join(cmd),
        "ok": proc.returncode == 0,
        "code": proc.returncode,
        "stdout": proc.stdout[-2000:],
        "stderr": proc.stderr[-2000:],
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run isolated PostgreSQL alembic migration replay on a scratch database cloned "
            "from POSTGRES_TEST_DATABASE_URL."
        )
    )
    parser.add_argument(
        "--output-json", default="", help="Optional path to write JSON evidence output."
    )
    args = parser.parse_args()

    allow_prodlike = os.environ.get("ALLOW_PRODLIKE_POSTGRES", "").lower() in {"1", "true", "yes"}
    base = _url(allow_prodlike=allow_prodlike)
    test_url = _clone_db_url(base, "_migration_smoke")
    env = os.environ.copy()
    env["DATABASE_URL"] = test_url
    # create/drop isolated db through base connection
    import sqlalchemy as sa

    admin = sa.create_engine(base, isolation_level="AUTOCOMMIT", future=True)
    dbname = urlparse(test_url).path.lstrip("/")
    with admin.connect() as c:
        c.execute(sa.text(f'DROP DATABASE IF EXISTS "{dbname}"'))
        c.execute(sa.text(f'CREATE DATABASE "{dbname}"'))
    checks: list[dict[str, object]] = []
    failed = False
    try:
        for cmd in (
            ["python", "-m", "alembic", "upgrade", "head"],
            ["python", "-m", "alembic", "downgrade", "base"],
            ["python", "-m", "alembic", "upgrade", "head"],
        ):
            result = _run_capture(cmd, env)
            checks.append(result)
            if not result["ok"]:
                failed = True
                break
    finally:
        with admin.connect() as c:
            c.execute(sa.text(f'DROP DATABASE IF EXISTS "{dbname}"'))
    output = {
        "ok": not failed,
        "allow_prodlike": allow_prodlike,
        "scratch_database": dbname,
        "checks": checks,
    }
    if args.output_json:
        with open(args.output_json, "w", encoding="utf-8") as fh:
            json.dump(output, fh, indent=2)
    print(f"Postgres migration smoke: {'PASS' if output['ok'] else 'FAIL'} (scratch_db={dbname})")
    print(json.dumps(output, indent=2))
    return 0 if output["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
