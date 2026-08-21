import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MATRIX = ROOT / "docs/frontend/migration/00_openapi_frontend_rendering_matrix.json"
OWNERSHIP = ROOT / "docs/frontend/migration/01_HTTP_CLIENT_OWNERSHIP_INPUT.json"


def test_authority_triage_fails_closed_and_assigns_exactly_one_http_owner() -> None:
    matrix = json.loads(MATRIX.read_text())
    ownership = json.loads(OWNERSHIP.read_text())
    operations = matrix["http_operations"]
    by_path = {(row["method"], row["path"]): row for row in operations}

    expected_deferred = {
        ("GET", "/market-time-machine"): "canonical_compatibility_ownership_unresolved",
        ("POST", "/api/v1/access/api-keys/{key_id}/freeze"): "access_security_contract_unresolved",
        ("POST", "/api/v1/auth/login"): "disabled_legacy_auth",
        ("POST", "/api/v1/auth/register"): "disabled_legacy_auth",
    }
    for key, reason in expected_deferred.items():
        row = by_path[key]
        assert row["disposition"] == "DEFERRED_WITH_REASON"
        assert row["authority_status"] == "DEFERRED_AUTHORITY"
        assert row["reason"] == reason
        assert row["typed_client_owner"] == "none"
        assert row["authority_future_owner"]
        assert row["authority_reentry_condition"]

    authoritative = ownership["authoritative_http_operations"]
    expected_authoritative = {
        row["operation_id"]
        for row in operations
        if row["authority_status"] == "AUTHORITATIVE_NOW"
        and row["disposition"] in {"UI_REQUIRED", "UI_OPTIONAL"}
    }
    assert {row["operation_id"] for row in authoritative} == expected_authoritative
    assert ownership["blocked_http_candidates"] == []
    assert len({row["owner"] for row in authoritative}) == len(authoritative)
    assert not any(row["path"].startswith("/api/v1/auth/") for row in authoritative)


def test_websocket_versions_are_backend_authoritative_and_owned_by_prompt_4() -> None:
    ownership = json.loads(OWNERSHIP.read_text())
    websockets = ownership["authoritative_websocket_contracts"]

    assert len(websockets) == 9
    assert sorted(row["authority_blocker_id"] for row in websockets) == [
        f"P1R2-B{number:02d}" for number in range(5, 14)
    ]
    assert all(row["authority_status"] == "AUTHORITATIVE_NOW" for row in websockets)
    assert all(row["authority_future_owner"] == "Prompt 4/25 (resolved)" for row in websockets)
    assert all(row["wire_version_authority"] == "1" for row in websockets)
    assert ownership["deferred_websocket_protocols"] == []
