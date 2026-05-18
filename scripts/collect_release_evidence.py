#!/usr/bin/env python
from __future__ import annotations
import argparse
import json
import os
import subprocess
from datetime import datetime, UTC

def run(cmd: str) -> dict[str, object]:
    p = subprocess.run(cmd, shell=True, text=True, capture_output=True)
    return {"cmd": cmd, "ok": p.returncode==0, "code": p.returncode, "stdout": p.stdout[-4000:], "stderr": p.stderr[-4000:]}

def main() -> int:
    parser = argparse.ArgumentParser(description="Collect release evidence into artifacts JSON file.")
    parser.add_argument(
        "--output",
        default="",
        help="Optional explicit artifact path. Defaults to artifacts/release_evidence_<sha>.json",
    )
    args = parser.parse_args()

    out = {
      "commit_sha": subprocess.check_output("git rev-parse HEAD", shell=True, text=True).strip(),
      "timestamp": datetime.now(UTC).isoformat(),
      "environment": os.environ.get("ENVIRONMENT","unknown"),
      "checks": [
        run("make lint"), run("python -m pytest -q"), run("make migration-smoke"), run("python scripts/run_postgres_migration_smoke.py"),
        run("python scripts/check_postgres_schema_parity.py"), run("python scripts/check_docs_truthfulness.py"),
      ],
      "health_readiness_result": run("python - <<'PY'\nprint('health/readiness check placeholder: use deployed API probes')\nPY"),
      "observability_snapshot": run("python - <<'PY'\nprint('observability snapshot requires running API env')\nPY"),
      "recovery_check": run("python - <<'PY'\nprint('recovery-check requires running API env')\nPY"),
      "metrics_scrape_result": run("python - <<'PY'\nprint('metrics scrape requires running API env')\nPY"),
      "known_limitations_acknowledgement": ["Some evidence fields require deployed environment/API credentials."]
    }
    os.makedirs("artifacts", exist_ok=True)
    path = args.output or f"artifacts/release_evidence_{out['commit_sha'][:8]}.json"
    with open(path,"w") as f: json.dump(out,f,indent=2)
    print(path)
    return 0
if __name__ == '__main__':
    raise SystemExit(main())
