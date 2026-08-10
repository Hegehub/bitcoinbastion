"""Deterministic semantic fingerprints for the Stage-1 handoff."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "docs/frontend/migration/00_openapi_frontend_rendering_matrix.json"
GENERATOR_PATHS = (
    "frontend/bastion_ui/transport/operation_compiler.py",
    "frontend/bastion_ui/transport/operation_emitter.py",
    "frontend/bastion_ui/transport/schema_compiler.py",
    "frontend/bastion_ui/transport/source_emitter.py",
    "scripts/analyze_http_generation_preflight.py",
    "scripts/generate_frontend_migration_audit.py",
    "scripts/generate_http_transport.py",
    "scripts/stage1_fingerprints.py",
)


def digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _file_records(paths: Iterable[Path], category: str) -> list[dict[str, str]]:
    return [
        {
            "path": path.relative_to(ROOT).as_posix(),
            "role": category,
            "sha256": digest_bytes(path.read_bytes()),
        }
        for path in sorted(paths)
    ]


def contract_records() -> list[dict[str, str]]:
    records = _file_records((ROOT / "app").rglob("*.py"), "contract_source")
    matrix = json.loads(MATRIX.read_text())
    selection = [
        {
            key: row.get(key)
            for key in (
                "matrix_id", "operation_id", "method", "path", "disposition",
                "authority_status", "product", "security_contract", "mutation_contract",
            )
        }
        for row in matrix["http_operations"]
    ]
    encoded = json.dumps(selection, sort_keys=True, separators=(",", ":")).encode()
    records.append({"path": "registry:http-operation-selection", "role": "contract_registry", "sha256": digest_bytes(encoded)})
    return records


def generator_records() -> list[dict[str, str]]:
    return _file_records((ROOT / path for path in GENERATOR_PATHS), "generator")


def manifest() -> dict[str, object]:
    contracts = contract_records()
    generators = generator_records()
    fingerprint = lambda rows: digest_bytes(json.dumps(rows, sort_keys=True, separators=(",", ":")).encode())
    return {
        "contract_source_fingerprint": fingerprint(contracts),
        "generator_fingerprint": fingerprint(generators),
        "inputs": contracts + generators,
    }


def source_revision() -> str:
    return subprocess.check_output(("git", "rev-parse", "HEAD"), cwd=ROOT, text=True).strip()


def dirty_stage1_inputs() -> list[str]:
    changed = subprocess.check_output(
        ("git", "status", "--porcelain", "--untracked-files=all"), cwd=ROOT, text=True
    ).splitlines()
    relevant = {row[3:] for row in changed}
    inputs = {record["path"] for record in manifest()["inputs"] if not record["path"].startswith("registry:")}
    return sorted(relevant & inputs)
