from fastapi.testclient import TestClient

from app.main import app


def test_candle_attribution_api_no_storage_smoke() -> None:
    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/api/v1/intelligence/candles/999999/top-events")

    assert response.status_code == 200
    assert "data" in response.json()


def test_candle_attribution_replay_api_no_storage_smoke() -> None:
    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/api/v1/intelligence/candles/999999/replay")

    assert response.status_code == 200
    assert "data" in response.json()


def test_candle_attribution_candidates_api_no_storage_smoke() -> None:
    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/api/v1/intelligence/candles/999999/candidates")

    assert response.status_code == 200
    assert "data" in response.json()


def test_candle_attribution_explain_api_no_storage_smoke() -> None:
    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/api/v1/intelligence/candles/999999/explain")

    assert response.status_code in {200, 404}
    assert response.json()


def test_candle_attribution_context_api_no_storage_smoke() -> None:
    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/api/v1/intelligence/candles/999999/context")

    assert response.status_code in {200, 404}
    assert response.json()
