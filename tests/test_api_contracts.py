from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_invalid_address_returns_standardized_code() -> None:
    r = client.get("/api/v1/trace/lite/not-a-btc-address")
    assert r.status_code == 400
    payload = r.json()
    assert payload["error"]["code"] in {"invalid_bitcoin_address", "http_error"}


def test_sensitive_input_returns_standardized_code() -> None:
    r = client.get(
        "/api/v1/trace/lite/abandon%20abandon%20abandon%20abandon%20abandon%20abandon%20abandon%20abandon%20abandon%20abandon%20abandon%20about"
    )
    assert r.status_code == 400
    payload = r.json()
    assert payload["error"]["code"] == "sensitive_wallet_material_not_accepted"
