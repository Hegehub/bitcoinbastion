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

    # Prompt 1B discovered that the prior descriptor names were only planned
    # owners: no strict error DTO or reviewed security metadata had been generated.
    assert ownership["authoritative_http_operations"] == []
    candidates = ownership["blocked_http_candidates"]
    assert len(candidates) == 309
    assert len({row["matrix_id"] for row in candidates}) == 309
    assert all(row["blocker_id"] == "P1B-B01" for row in candidates)
    assert not any(row["path"].startswith("/api/v1/auth/") for row in candidates)


def test_websocket_versions_are_not_invented_and_are_owned_by_prompt_4() -> None:
    ownership = json.loads(OWNERSHIP.read_text())
    websockets = ownership["deferred_websocket_protocols"]

    assert len(websockets) == 9
    assert [row["authority_blocker_id"] for row in websockets] == [
        f"P1R2-B{number:02d}" for number in range(5, 14)
    ]
    assert all(row["authority_status"] == "DEFERRED_AUTHORITY" for row in websockets)
    assert all(row["authority_future_owner"] == "Prompt 4/25" for row in websockets)
    assert all(row["wire_version_authority"] == "unavailable" for row in websockets)
