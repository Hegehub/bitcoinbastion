from fastapi.testclient import TestClient

from app.api.dependencies import get_admin_user
from app.main import app


class FakeAdminUser:
    is_admin = True


def test_policy_execution_summary_contract_shape() -> None:
    app.dependency_overrides[get_admin_user] = lambda: FakeAdminUser()
    client = TestClient(app)
    try:
        response = client.get("/api/v1/policy/executions/summary")
        assert response.status_code == 200
        payload = response.json()["data"]

        assert {"total", "allowed", "blocked", "allow_rate", "by_policy"} <= set(payload.keys())
        assert isinstance(payload["total"], int)
        assert isinstance(payload["allowed"], int)
        assert isinstance(payload["blocked"], int)
        assert 0.0 <= float(payload["allow_rate"]) <= 1.0
        assert isinstance(payload["by_policy"], list)

        for item in payload["by_policy"]:
            assert {"policy_name", "total", "allowed", "blocked"} <= set(item.keys())
    finally:
        app.dependency_overrides.clear()


def test_onchain_state_contract_includes_provenance_marker() -> None:
    client = TestClient(app)
    response = client.get("/api/v1/onchain/state")

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["finality_band"] in {"weak", "moderate", "strong"}
    assert "explainability" in data
    assert data["explainability"]["data_source"] in {"query", "repository_fallback"}
