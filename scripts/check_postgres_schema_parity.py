#!/usr/bin/env python
from __future__ import annotations
import os, sys, json
from urllib.parse import urlparse
from sqlalchemy import create_engine, inspect, text

REPO_ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, REPO_ROOT)
from scripts.check_schema_runtime_parity import collect_schema_parity_errors

BLOCKED_HOST_TOKENS = ("prod", "primary", "writer", "amazonaws.com")
BLOCKED_DB_TOKENS = ("prod", "production", "main")

def _require_url() -> str:
    url = os.environ.get("POSTGRES_TEST_DATABASE_URL", "").strip()
    if not url:
        raise SystemExit("POSTGRES_TEST_DATABASE_URL is required")
    if not url.startswith("postgresql"):
        raise SystemExit("POSTGRES_TEST_DATABASE_URL must be a PostgreSQL URL")
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    db = (parsed.path or "").lstrip("/").lower()
    allow = os.environ.get("ALLOW_PRODLIKE_POSTGRES", "").lower() in {"1","true","yes"}
    risky = any(t in host for t in BLOCKED_HOST_TOKENS) or any(t in db for t in BLOCKED_DB_TOKENS)
    if risky and not allow:
        raise SystemExit("Refusing prod-like Postgres target. Set ALLOW_PRODLIKE_POSTGRES=1 to override.")
    return url

def main() -> int:
    url = _require_url()
    engine = create_engine(url, future=True)
    insp = inspect(engine)
    errors = collect_schema_parity_errors(insp)
    result = {"ok": not errors, "error_count": len(errors), "errors": errors}
    print(json.dumps(result, indent=2))
    return 0 if not errors else 1

if __name__ == "__main__":
    raise SystemExit(main())
