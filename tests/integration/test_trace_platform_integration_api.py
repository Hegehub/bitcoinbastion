from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_trace_status_endpoint() -> None:
    r = client.get("/api/v1/trace/status")
    assert r.status_code == 200
    assert r.json()["data"]["trace_production_calibrated"] is False


def test_treasury_destination_check_endpoint() -> None:
    r = client.post(
        "/api/v1/trace/treasury/destination-check",
        json={"destination_address": "bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kg3g4ty"},
    )
    assert r.status_code == 200
    assert "no_transaction_signing" in r.json()["data"]["limitations"]


def test_register_payment_advisory_endpoint() -> None:
    r = client.post(
        "/api/v1/trace/register/payment-advisory",
        json={"payer_address": "1BoatSLRHtKNngkdXEeobR76b53LETtpyT"},
    )
    assert r.status_code == 200
    assert r.json()["data"]["merchant_recommendation"]
