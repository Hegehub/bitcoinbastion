#!/usr/bin/env python3
"""Generate the complete authoritative HTTP schema and operation package."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "frontend")]

from app.main import app  # noqa: E402
from bastion_ui.transport.operation_compiler import compile_operations  # noqa: E402
from bastion_ui.transport.operation_emitter import (  # noqa: E402
    OperationModulePlan,
    emit_operations,
)
from bastion_ui.transport.schema_compiler import OpenAPISchemaCompiler  # noqa: E402
from bastion_ui.transport.source_emitter import ModulePlan, emit_module  # noqa: E402

MATRIX = ROOT / "docs/frontend/migration/00_openapi_frontend_rendering_matrix.json"
OUT = ROOT / "frontend/bastion_ui/transport"


def render() -> dict[Path, str]:
    spec = app.openapi()
    matrix = json.loads(MATRIX.read_text())
    rows = [
        row
        for row in matrix["http_operations"]
        if row["disposition"] in {"UI_REQUIRED", "UI_OPTIONAL"}
        and row.get("authority_status") == "AUTHORITATIVE_NOW"
    ]
    schemas = OpenAPISchemaCompiler(spec["components"]["schemas"]).compile_all()
    operations = compile_operations(spec, rows)
    source_revision = str(matrix["metadata"]["head"])
    return {
        OUT / "generated_schemas.py": emit_module(ModulePlan.build(schemas)),
        OUT / "generated_http.py": emit_operations(
            OperationModulePlan.build(operations, source_revision=source_revision)
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args()
    outputs = render()
    stale = [path for path, source in outputs.items() if not path.exists() or path.read_text() != source]
    if args.check:
        if stale:
            raise SystemExit("stale generated transport files: " + ", ".join(map(str, stale)))
        return
    for path, source in outputs.items():
        path.write_text(source)


if __name__ == "__main__":
    main()
