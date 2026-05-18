#!/usr/bin/env python
from __future__ import annotations
import argparse
import json
import os
import sys
from urllib.parse import urlparse
from sqlalchemy import create_engine, inspect, text

REPO_ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, REPO_ROOT)
from scripts.check_schema_runtime_parity import collect_schema_parity_errors

BLOCKED_HOST_TOKENS = ("prod", "primary", "writer", "amazonaws.com")
BLOCKED_DB_TOKENS = ("prod", "production", "main")

def _require_url(*, allow_prodlike: bool) -> str:
    url = os.environ.get("POSTGRES_TEST_DATABASE_URL", "").strip()
    if not url:
        raise SystemExit("POSTGRES_TEST_DATABASE_URL is required")
    if not url.startswith("postgresql"):
        raise SystemExit("POSTGRES_TEST_DATABASE_URL must be a PostgreSQL URL")
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    db = (parsed.path or "").lstrip("/").lower()
    risky = any(t in host for t in BLOCKED_HOST_TOKENS) or any(t in db for t in BLOCKED_DB_TOKENS)
    if risky and not allow_prodlike:
        raise SystemExit("Refusing prod-like Postgres target. Set ALLOW_PRODLIKE_POSTGRES=1 to override.")
    return url

def _bool_env(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes"}

def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Validate PostgreSQL runtime schema parity against SQLAlchemy models using "
            "POSTGRES_TEST_DATABASE_URL."
        )
    )
    parser.add_argument(
        "--output-json",
        default="",
        help="Optional path to write machine-readable JSON report.",
    )
    args = parser.parse_args()

    allow_prodlike = _bool_env("ALLOW_PRODLIKE_POSTGRES")
    url = _require_url(allow_prodlike=allow_prodlike)
    engine = create_engine(url, future=True)
    insp = inspect(engine)
    errors = collect_schema_parity_errors(insp)
    result = {
        "ok": not errors,
        "error_count": len(errors),
        "errors": errors,
        "target": {
            "host": (urlparse(url).hostname or "unknown"),
            "database": (urlparse(url).path or "").lstrip("/") or "unknown",
        },
    }
    if args.output_json:
        with open(args.output_json, "w", encoding="utf-8") as fh:
            json.dump(result, fh, indent=2)

    print(
        f"Postgres schema parity: {'PASS' if result['ok'] else 'FAIL'} "
        f"(errors={result['error_count']}, allow_prodlike={allow_prodlike})"
    )
    print(json.dumps(result, indent=2))
    return 0 if not errors else 1

if __name__ == "__main__":
    raise SystemExit(main())
