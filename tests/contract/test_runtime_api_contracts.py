from fastapi.testclient import TestClient

from app.api.dependencies import get_admin_user
from app.db.base import Base
from app.db.models.signal import Signal
from app.db.repositories.signal_repository import SignalRepository
from app.db.session import SessionLocal, engine
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


def test_policy_execution_summary_contract_rejects_invalid_limit() -> None:
    app.dependency_overrides[get_admin_user] = lambda: FakeAdminUser()
    client = TestClient(app)
    try:
        response = client.get("/api/v1/policy/executions/summary", params={"limit": 0})
        assert response.status_code == 422
    finally:
        app.dependency_overrides.clear()


def test_policy_execution_summary_contract_rejects_limit_above_max() -> None:
    app.dependency_overrides[get_admin_user] = lambda: FakeAdminUser()
    client = TestClient(app)
    try:
        response = client.get("/api/v1/policy/executions/summary", params={"limit": 1001})
        assert response.status_code == 422
    finally:
        app.dependency_overrides.clear()


def test_policy_execution_summary_contract_requires_admin_auth() -> None:
    client = TestClient(app)
    response = client.get("/api/v1/policy/executions/summary")
    assert response.status_code in {401, 403}


def test_onchain_state_contract_includes_provenance_marker() -> None:
    client = TestClient(app)
    response = client.get("/api/v1/onchain/state")

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["finality_band"] in {"weak", "moderate", "strong"}
    assert "explainability" in data
    assert data["explainability"]["data_source"] in {"query", "repository_fallback"}


def test_signal_explanation_contract_includes_source_evidence_graph_when_linked() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        signal = Signal(
            signal_type="news",
            title="Contract source-linked signal",
            score=0.82,
            confidence=0.71,
            explainability_json="{}",
        )
        signal = SignalRepository(db).add_with_source(
            signal=signal,
            source_type="news",
            source_id="contract-article-1",
            weight=1.0,
        )
        signal_id = signal.id

    client = TestClient(app)
    response = client.get(f"/api/v1/signals/{signal_id}/explanation")

    assert response.status_code == 200
    data = response.json()["data"]
    assert isinstance(data["nodes"], list)
    assert isinstance(data["edges"], list)
    assert any(item["node_type"] == "source" for item in data["nodes"])
    assert any(item["relation"] == "supports" for item in data["edges"])
