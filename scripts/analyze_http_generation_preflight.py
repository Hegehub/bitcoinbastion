#!/usr/bin/env python3
"""Deterministically inventory Prompt-1B0R full-generation capabilities and blockers."""

from __future__ import annotations

from collections import Counter, defaultdict
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "frontend"))
from app.main import app  # noqa: E402
from bastion_ui.transport.schema_compiler import (  # noqa: E402
    OpenAPISchemaCompiler,
    SchemaCompileError,
)

DOCS = ROOT / "docs/frontend/migration"
MATRIX = DOCS / "00_openapi_frontend_rendering_matrix.json"
OUT = DOCS / "01B0_GENERATION_PREFLIGHT.json"
MUTATION_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
SCHEMA_KEYS = {
    "$ref",
    "type",
    "format",
    "enum",
    "const",
    "allOf",
    "oneOf",
    "anyOf",
    "discriminator",
    "additionalProperties",
    "nullable",
    "pattern",
    "minimum",
    "maximum",
    "minLength",
    "maxLength",
    "minItems",
    "maxItems",
    "readOnly",
    "writeOnly",
    "default",
    "deprecated",
}


def _walk(
    value: object,
    counts: Counter[str],
    examples: dict[str, set[str]],
    owner: str,
    schemas: dict[str, Any],
    visited_refs: set[str],
) -> None:
    if isinstance(value, dict):
        for key in SCHEMA_KEYS.intersection(value):
            counts[key] += 1
            examples[key].add(owner)
        value_type = value.get("type")
        if isinstance(value_type, str) and value_type in {
            "string",
            "integer",
            "number",
            "boolean",
            "array",
            "object",
            "null",
        }:
            kind = f"type:{value_type}"
            counts[kind] += 1
            examples[kind].add(owner)
        reference = value.get("$ref")
        if isinstance(reference, str) and reference.startswith("#/components/schemas/"):
            schema_name = reference.rsplit("/", 1)[-1]
            if schema_name not in visited_refs:
                visited_refs.add(schema_name)
                _walk(schemas[schema_name], counts, examples, owner, schemas, visited_refs)
        for key, child in value.items():
            if key != "$ref":
                _walk(child, counts, examples, owner, schemas, visited_refs)
    elif isinstance(value, list):
        for child in value:
            _walk(child, counts, examples, owner, schemas, visited_refs)


def _contains_key(value: object, target: str) -> bool:
    if isinstance(value, dict):
        return target in value or any(_contains_key(child, target) for child in value.values())
    if isinstance(value, list):
        return any(_contains_key(child, target) for child in value)
    return False


def _reachable_refs(value: object, schemas: dict[str, Any]) -> set[str]:
    refs: set[str] = set()

    def collect(node: object) -> None:
        if isinstance(node, dict):
            reference = node.get("$ref")
            if isinstance(reference, str) and reference.startswith("#/components/schemas/"):
                name = reference.rsplit("/", 1)[-1]
                if name not in refs:
                    refs.add(name)
                    collect(schemas[name])
            for child in node.values():
                collect(child)
        elif isinstance(node, list):
            for child in node:
                collect(child)

    collect(value)
    return refs


def build_report() -> dict[str, Any]:
    spec = app.openapi()
    matrix = json.loads(MATRIX.read_text())
    schemas = spec.get("components", {}).get("schemas", {})
    candidates = [
        row
        for row in matrix["http_operations"]
        if row["disposition"] in {"UI_REQUIRED", "UI_OPTIONAL"}
        and row.get("authority_status") == "AUTHORITATIVE_NOW"
    ]
    security_deferred = [
        row
        for row in matrix["http_operations"]
        if row.get("deferred_contract_kind") in {"protected", "protected_mutation"}
    ]
    mutation_deferred = [
        row
        for row in matrix["http_operations"]
        if row.get("deferred_contract_kind") in {"mutation", "protected_mutation"}
    ]
    schema_counts: Counter[str] = Counter()
    examples: dict[str, set[str]] = defaultdict(set)
    media_counts: Counter[str] = Counter()
    success_counts: Counter[str] = Counter()
    protected: list[dict[str, str]] = []
    mutations: list[dict[str, str]] = []
    blockers: list[dict[str, str]] = []
    schema_consumers: dict[str, set[str]] = defaultdict(set)
    html_operations: list[dict[str, str]] = []
    no_content_operations: list[dict[str, str]] = []
    deferred_no_content_operations: list[dict[str, str]] = []
    for row in candidates:
        operation = spec["paths"][row["path"]][row["method"].lower()]
        owner = row["operation_id"]
        for schema_name in _reachable_refs(operation, schemas):
            schema_consumers[schema_name].add(owner)
        _walk(operation, schema_counts, examples, owner, schemas, set())
        for status, response in operation.get("responses", {}).items():
            if not status.startswith("2"):
                continue
            success_counts[status] += 1
            content = response.get("content", {})
            if not content and status == "204":
                media_counts["no-content"] += 1
                no_content_operations.append(
                    {"matrix_id": row["matrix_id"], "operation_id": owner, "path": row["path"]}
                )
            for media in content:
                media_counts[media] += 1
                if media == "text/html":
                    html_operations.append(
                        {"matrix_id": row["matrix_id"], "operation_id": owner, "path": row["path"]}
                    )
        if row["access_class"] == "protected":
            protected.append(
                {"matrix_id": row["matrix_id"], "operation_id": owner, "path": row["path"]}
            )
            blockers.append(
                {
                    "operation_id": owner,
                    "blocker": "P1B0-B01",
                    "missing": "reviewed dependency-level scope/PoP/signing/intent/step-up/replay metadata",
                }
            )
        if row["method"] in MUTATION_METHODS:
            mutations.append(
                {
                    "matrix_id": row["matrix_id"],
                    "operation_id": owner,
                    "method": row["method"],
                    "path": row["path"],
                }
            )
            blockers.append(
                {
                    "operation_id": owner,
                    "blocker": "P1B0-B02",
                    "missing": "source-backed idempotency, retry, replay, Human Intent, and reconciliation semantics",
                }
            )
    for row in matrix["http_operations"]:
        if row.get("success_status") == "204" and row["disposition"] == "DEFERRED_WITH_REASON":
            deferred_no_content_operations.append(
                {
                    "matrix_id": row["matrix_id"],
                    "operation_id": row["operation_id"],
                    "method": row["method"],
                    "path": row["path"],
                    "blocker_id": row.get("authority_blocker_id", ""),
                }
            )
    unsupported = sorted(
        key
        for key in schema_counts
        if key in {"allOf", "oneOf", "anyOf", "discriminator", "additionalProperties"}
    )
    protected_ids = {row["operation_id"] for row in protected}
    mutation_ids = {row["operation_id"] for row in mutations}
    protected_mutations = protected_ids & mutation_ids
    construct_schemas = {
        key: sorted(name for name, schema in schemas.items() if _contains_key(schema, key))
        for key in ("anyOf", "additionalProperties")
    }
    compiler = OpenAPISchemaCompiler(schemas)
    compiler_failures: list[dict[str, object]] = []
    for schema_name in sorted(schemas):
        try:
            compiler.compile_component(schema_name)
        except SchemaCompileError as exc:
            compiler_failures.append(
                {
                    "schema_id": schema_name,
                    "error": str(exc),
                    "active_consumers": sorted(schema_consumers[schema_name]),
                }
            )
    if not compiler_failures:
        unsupported = []
    return {
        "counts": {
            "runtime_http": sum(
                1
                for item in spec["paths"].values()
                for method in item
                if method.lower()
                in {"get", "post", "put", "patch", "delete", "head", "options", "trace"}
            ),
            "generation_candidates": len(candidates),
            "security_deferred": len(security_deferred),
            "mutation_deferred": len(mutation_deferred),
            "protected_candidates": len(protected),
            "mutation_candidates": len(mutations),
            "protected_only": len(protected_ids - mutation_ids),
            "mutation_only": len(mutation_ids - protected_ids),
            "protected_mutations": len(protected_mutations),
            "b01_b02_unique_operations": len(protected_ids | mutation_ids),
            "ready": len(candidates) - len({b["operation_id"] for b in blockers}),
            "security_blocked": len(protected),
            "mutation_blocked": len(mutations),
            "schema_capabilities_unproven": len(unsupported),
        },
        "protected_operations": protected,
        "mutations": mutations,
        "security_deferred_operations": security_deferred,
        "mutation_deferred_operations": mutation_deferred,
        "html_operations": html_operations,
        "no_content_operations": no_content_operations,
        "deferred_no_content_operations": deferred_no_content_operations,
        "schema_vocabulary": {
            key: {"count": schema_counts[key], "operations": sorted(examples[key])}
            for key in sorted(schema_counts)
        },
        "construct_schema_ids": construct_schemas,
        "schema_compiler": {
            "components": len(schemas),
            "compiled": len(schemas) - len(compiler_failures),
            "failures": compiler_failures,
            "cycles": compiler.cycles(),
        },
        "response_vocabulary": {
            "success_statuses": dict(sorted(success_counts.items())),
            "media_types": dict(sorted(media_counts.items())),
        },
        "unproven_schema_capabilities": unsupported,
        "blockers": sorted(blockers, key=lambda row: (row["operation_id"], row["blocker"])),
        "websocket_authority": "AUTHORITATIVE_PROMPT_4; backend WireFrame v1 registry owns nine routes",
    }


def main() -> None:
    rendered = json.dumps(build_report(), indent=2, sort_keys=True) + "\n"
    if "--check" in sys.argv:
        if not OUT.exists() or OUT.read_text() != rendered:
            raise SystemExit("generation preflight is stale; run with --write")
    elif "--write" in sys.argv:
        OUT.write_text(rendered)
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()
