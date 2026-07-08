from fastapi.testclient import TestClient

from app.db.base import Base
from app.db.models.signal import Signal
from app.db.repositories.signal_repository import SignalRepository
from app.db.session import SessionLocal, engine
from app.main import app
from tests.helpers.access import ACCESS_HEADERS, proof_of_access_overrides


def test_policy_execution_summary_contract_shape() -> None:
    client = TestClient(app)
    with proof_of_access_overrides():
        response = client.get("/api/v1/policy/executions/summary", headers=ACCESS_HEADERS)
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


def test_policy_execution_summary_contract_rejects_invalid_limit() -> None:
    client = TestClient(app)
    with proof_of_access_overrides():
        response = client.get(
            "/api/v1/policy/executions/summary", headers=ACCESS_HEADERS, params={"limit": 0}
        )
        assert response.status_code == 422


def test_policy_execution_summary_contract_rejects_limit_above_max() -> None:
    client = TestClient(app)
    with proof_of_access_overrides():
        response = client.get(
            "/api/v1/policy/executions/summary", headers=ACCESS_HEADERS, params={"limit": 1001}
        )
        assert response.status_code == 422


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
    assert data["explainability"]["data_source"] in {
        "query",
        "repository_fallback",
        "provider_probe",
        "provider_fallback",
    }


def test_paginated_envelope_contract_for_top_signals() -> None:
    client = TestClient(app)
    response = client.get("/api/v1/signals/top")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert set(payload.keys()) == {"success", "data"}
    assert set(payload["data"].keys()) == {"items", "total", "limit", "offset"}
    assert isinstance(payload["data"]["items"], list)
    assert isinstance(payload["data"]["total"], int)
    assert isinstance(payload["data"]["limit"], int)
    assert isinstance(payload["data"]["offset"], int)


def test_health_endpoints_are_intentional_non_envelope_exceptions() -> None:
    client = TestClient(app)

    for path in ["/api/v1/health", "/api/v1/health/live", "/api/v1/health/ready"]:
        response = client.get(path)
        assert response.status_code == 200
        payload = response.json()
        assert "status" in payload
        assert "app" in payload
        assert "success" not in payload


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
