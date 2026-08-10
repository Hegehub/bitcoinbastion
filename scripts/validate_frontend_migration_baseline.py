#!/usr/bin/env python3
"""Validate deterministic Prompt-0 migration invariants without claiming UI parity."""

from __future__ import annotations

import json
import hashlib
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs/frontend/migration"


def main() -> None:
    matrix = json.loads((DOCS / "00_openapi_frontend_rendering_matrix.json").read_text())
    operations = matrix["http_operations"]
    websockets = matrix["websocket_channels"]
    ids = [row["matrix_id"] for row in operations + websockets]
    assert (
        len(ids) == len(set(ids)) == matrix["counts"]["operations"] + matrix["counts"]["websockets"]
    )
    allowed_dispositions = {
        "UI_REQUIRED",
        "UI_OPTIONAL",
        "BACKEND_ONLY",
        "CALLBACK_ONLY",
        "PROTOCOL_ONLY",
        "SEPARATE_PRODUCT",
        "DEFERRED_WITH_REASON",
    }
    allowed_coverage = {
        "NOT_STARTED",
        "CLIENT_ONLY",
        "ADAPTER_ONLY",
        "STATE_ONLY",
        "TRIGGER_ONLY",
        "RENDER_ONLY",
        "FIXTURE_RENDERED",
        "PARTIAL",
        "IMPLEMENTED_UNVERIFIED",
        "IMPLEMENTED_VERIFIED",
        "UNAVAILABLE",
        "NOT_APPLICABLE",
    }
    for row in operations + websockets:
        assert row["disposition"] in allowed_dispositions
        assert row["coverage_state"] in allowed_coverage
        prompt = row.get("implementation_prompt")
        assert prompt is None or 1 <= prompt <= 25

    authoritative_ui = [
        row
        for row in operations
        if row["authority_status"] == "AUTHORITATIVE_NOW"
        and row["disposition"] in {"UI_REQUIRED", "UI_OPTIONAL"}
    ]
    deferred = [
        row for row in operations + websockets if row["authority_status"] == "DEFERRED_AUTHORITY"
    ]
    assert all(
        row["typed_client_owner"].startswith("bastion_ui.transport.generated_http:")
        for row in authoritative_ui
    )
    assert len({row["typed_client_owner"] for row in authoritative_ui}) == len(authoritative_ui)
    assert all(row.get("authority_blocker_id") for row in deferred)
    assert all(row.get("authority_future_owner") for row in deferred)
    assert all(row.get("authority_reentry_condition") for row in deferred)
    assert all(row.get("typed_client_owner", "none") == "none" for row in deferred)
    assert all(row.get("wire_version_authority") == "1" for row in websockets)
    assert all(row.get("authority_status") == "AUTHORITATIVE_NOW" for row in websockets)

    ownership = json.loads((DOCS / "01_HTTP_CLIENT_OWNERSHIP_INPUT.json").read_text())
    assert len(ownership["authoritative_websocket_contracts"]) == 9
    assert ownership["deferred_websocket_protocols"] == []
    assert len(ownership["authoritative_http_operations"]) == len(authoritative_ui)
    assert ownership["blocked_http_candidates"] == []
    assert len(authoritative_ui) == 194
    assert all(row["coverage_state"] == "CLIENT_ONLY" for row in authoritative_ui)

    transport = ROOT / "frontend/bastion_ui/transport"
    manifest = json.loads((transport / "generated_manifest.json").read_text())
    assert manifest["operation_count"] == len(authoritative_ui)
    for name, digest in manifest["files"].items():
        assert hashlib.sha256((transport / name).read_bytes()).hexdigest() == digest

    feature_text = (DOCS / "00_69_FEATURE_REGISTER.md").read_text()
    feature_ids = [int(v) for v in re.findall(r"^\| (\d{2}) \|", feature_text, re.M)]
    assert feature_ids == list(range(1, 70))

    migration_text = (DOCS / "00_PROMPT_MIGRATION_0_52_TO_0_25.md").read_text()
    mappings = [
        (int(a), int(b))
        for a, b in re.findall(r"^\| (\d+) \| (\d+) \| mapped", migration_text, re.M)
    ]
    assert [old for old, _ in mappings] == list(range(53))
    assert set(new for _, new in mappings) == set(range(26))
    print(
        f"PASS: {len(operations)} HTTP + {len(websockets)} WS records; "
        f"{len(authoritative_ui)} authoritative UI HTTP; {len(deferred)} deferred; "
        "69 features; 53 prompt mappings"
    )


if __name__ == "__main__":
    main()
