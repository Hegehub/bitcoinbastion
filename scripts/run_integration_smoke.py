#!/usr/bin/env python3
"""Run static integration smoke checks and write evidence artifacts."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "artifacts" / "integration_smoke.json"
SDK_ARTIFACT = ROOT / "artifacts" / "sdk_smoke.json"


def run(cmd: list[str]) -> dict[str, object]:
    proc = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, timeout=120)
    return {"command": " ".join(cmd), "returncode": proc.returncode, "stdout": proc.stdout[-4000:], "stderr": proc.stderr[-4000:]}


def file_status(paths: list[str]) -> dict[str, str]:
    return {p: "implemented" if (ROOT / p).exists() else "blocked" for p in paths}


def main() -> int:
    scripts = [
        [sys.executable, "scripts/check_route_api_parity.py"],
        [sys.executable, "scripts/check_runtime_profiles.py"],
        [sys.executable, "scripts/check_frontend_contracts.py"],
    ]
    script_runs = [run(cmd) for cmd in scripts]
    sdk = {
        "python_sdk": file_status([
            "sdk/python/bitcoin_bastion_sdk/client.py", "sdk/python/bitcoin_bastion_sdk/resources/trace.py",
            "sdk/python/bitcoin_bastion_sdk/resources/webhooks.py", "sdk/python/bitcoin_bastion_sdk/websocket.py",
        ]),
        "typescript_sdk": file_status(["sdk/typescript/package.json", "sdk/typescript/src/client.ts", "sdk/typescript/src/resources/trace.ts"]),
        "cli": file_status(["cli/bastion_cli/main.py", "pyproject.toml"]),
        "mcp": file_status(["mcp/bastion_mcp/server.py", "mcp/pyproject.toml"]),
        "plugins": file_status(["app/plugins/base.py", "app/plugins/registry.py", "app/plugins/permissions.py", "app/plugins/sandbox.py"]),
    }
    SDK_ARTIFACT.parent.mkdir(exist_ok=True)
    SDK_ARTIFACT.write_text(json.dumps(sdk, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    blockers = [r["command"] for r in script_runs if r["returncode"] != 0]
    for group, entries in sdk.items():
        missing = [path for path, status in entries.items() if status == "blocked"]
        if missing and group in {"python_sdk", "plugins"}:
            blockers.append(f"{group}:{','.join(missing)}")
    result = {"status": "implemented" if not blockers else "blocked", "script_runs": script_runs, "sdk_cli_mcp_plugin_status": sdk, "blockers": blockers}
    ARTIFACT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 1 if blockers else 0

if __name__ == "__main__":
    raise SystemExit(main())
