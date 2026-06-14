from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from fastapi.testclient import TestClient

from app.api.dependencies import get_admin_user
from app.main import app


@contextmanager
def admin_client() -> Iterator[TestClient]:
    app.dependency_overrides[get_admin_user] = lambda: object()
    try:
        with TestClient(app) as client:
            yield client
    finally:
        app.dependency_overrides.pop(get_admin_user, None)


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
    with admin_client() as client:
        client.post("/api/v1/plugins/builtin.dashboard.status/enable")
        response = client.post(
            "/api/v1/plugins/builtin.dashboard.status/dry-run",
            json={"payload": {"message": "bounded smoke"}},
        )

    assert response.status_code == 200
    data = response_data(response.json())
    assert data["dry_run"] is True
    assert data["safety_flags"]["no_custody"] is True


def test_dry_run_forbidden_input_rejected() -> None:
    with admin_client() as client:
        response = client.post(
            "/api/v1/plugins/builtin.dashboard.status/dry-run",
            json={"payload": {"bad": "private key should never be submitted"}},
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
