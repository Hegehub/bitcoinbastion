#!/usr/bin/env python3
"""Validate that Stage-1 artifacts share one truthful source state."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "frontend")]

from app.main import app  # noqa: E402
from scripts.stage1_fingerprints import manifest as current_source_manifest  # noqa: E402

DOCS = ROOT / "docs/frontend/migration"
TRANSPORT = ROOT / "frontend/bastion_ui/transport"
def git(*args: str) -> str:
    return subprocess.check_output(("git", *args), cwd=ROOT, text=True).strip()


def semantic_digest(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def main() -> None:
    snapshot = json.loads((DOCS / "00_OPENAPI_SNAPSHOT.json").read_text())
    matrix = json.loads((DOCS / "00_openapi_frontend_rendering_matrix.json").read_text())
    ownership = json.loads((DOCS / "01_HTTP_CLIENT_OWNERSHIP_INPUT.json").read_text())
    manifest = json.loads((TRANSPORT / "generated_manifest.json").read_text())
    revisions = {
        "snapshot": snapshot["metadata"]["head"],
        "matrix": matrix["metadata"]["head"],
        "ownership": ownership["metadata"]["head"],
        "manifest": manifest["source_revision"],
    }
    if len(set(revisions.values())) != 1:
        raise SystemExit(f"Stage-1 revision mismatch: {revisions}")
    source_revision = next(iter(revisions.values()))
    recorded_contract = manifest.get("contract_source_fingerprint")
    recorded_generator = manifest.get("generator_fingerprint")
    current = current_source_manifest()
    if recorded_contract != current["contract_source_fingerprint"]:
        raise SystemExit("STALE_SOURCE_INPUTS: contract source fingerprint differs")
    if recorded_generator != current["generator_fingerprint"]:
        raise SystemExit("STALE_GENERATOR: generator fingerprint differs")
    for artifact_name, artifact in (("snapshot", snapshot), ("matrix", matrix), ("ownership", ownership)):
        metadata = artifact["metadata"]
        if metadata.get("contract_source_fingerprint") != recorded_contract:
            raise SystemExit(f"INVALID_ARTIFACT: {artifact_name} contract fingerprint differs")
        if metadata.get("generator_fingerprint") != recorded_generator:
            raise SystemExit(f"INVALID_ARTIFACT: {artifact_name} generator fingerprint differs")

    runtime_openapi = app.openapi()
    if snapshot["openapi"] != runtime_openapi:
        raise SystemExit("runtime OpenAPI differs from the Stage-1 snapshot")
    if manifest["openapi_sha256"] != semantic_digest(runtime_openapi):
        raise SystemExit("generated manifest OpenAPI digest is stale")
    for name, digest in manifest["files"].items():
        if hashlib.sha256((TRANSPORT / name).read_bytes()).hexdigest() != digest:
            raise SystemExit(f"generated file digest mismatch: {name}")

    current_head = git("rev-parse", "HEAD")
    status = "VALID_CURRENT_REVISION" if source_revision == current_head else "VALID_UNCHANGED_SOURCE"
    print(
        f"PASS: {status}; Stage-1 source revision "
        f"{source_revision}; OpenAPI {manifest['openapi_sha256']}; "
        f"{manifest['operation_count']} operations; {manifest['schema_count']} schemas; "
        f"contract {recorded_contract}; generator {recorded_generator}"
    )


if __name__ == "__main__":
    main()
