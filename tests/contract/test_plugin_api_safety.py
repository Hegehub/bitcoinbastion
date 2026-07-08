from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from fastapi.testclient import TestClient

from app.main import app
from tests.helpers.access import ACCESS_HEADERS, SIGNED_ACCESS_HEADERS, proof_of_access_overrides


@contextmanager
def access_client() -> Iterator[TestClient]:
    with proof_of_access_overrides():
        with TestClient(app) as client:
            yield client


def response_data(response_json: dict[str, Any]) -> dict[str, Any]:
    assert response_json["success"] is True
    return response_json["data"]


def test_list_plugins_works_and_includes_safety_fields() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/plugins")

    assert response.status_code == 200
    data = response_data(response.json())
    assert data["items"]
    assert "limitations" in data
    assert "safety_flags" in data
    assert data["safety_flags"]["no_custody"] is True


def test_get_plugin_works() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/plugins/builtin.dashboard.status")

    assert response.status_code == 200
    data = response_data(response.json())
    assert data["plugin_id"] == "builtin.dashboard.status"
    assert "limitations" in data
    assert "safety_flags" in data


def test_enable_requires_admin() -> None:
    with TestClient(app) as client:
        response = client.post("/api/v1/plugins/builtin.dashboard.status/enable")

    assert response.status_code in {401, 403}


def test_disable_requires_admin() -> None:
    with TestClient(app) as client:
        response = client.post("/api/v1/plugins/builtin.dashboard.status/disable")

    assert response.status_code in {401, 403}


def test_dry_run_does_not_perform_risky_action() -> None:
    with access_client() as client:
        client.post(
            "/api/v1/plugins/builtin.dashboard.status/enable", headers=SIGNED_ACCESS_HEADERS
        )
        response = client.post(
            "/api/v1/plugins/builtin.dashboard.status/dry-run",
            json={"payload": {"message": "bounded smoke"}},
            headers=ACCESS_HEADERS,
        )

    assert response.status_code == 200
    data = response_data(response.json())
    assert data["dry_run"] is True
    assert data["safety_flags"]["no_custody"] is True


def test_dry_run_forbidden_input_rejected() -> None:
    with access_client() as client:
        response = client.post(
            "/api/v1/plugins/builtin.dashboard.status/dry-run",
            json={"payload": {"bad": "private key should never be submitted"}},
            headers=ACCESS_HEADERS,
        )

    assert response.status_code == 400


def test_plugin_api_responses_do_not_offer_risky_actions() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/plugins")

    body = response.text.lower()
    assert "sign transactions" in body
    assert "broadcast transactions" in body
    assert "approve treasury actions" in body
    assert "seed phrase" not in body
    assert "private key" not in body
