from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_trace_events_endpoint_works() -> None:
    client.get("/api/v1/trace/address/1BoatSLRHtKNngkdXEeobR76b53LETtpyT")
    r = client.get("/api/v1/trace/events")
    assert r.status_code == 200
    assert isinstance(r.json()["data"], list)


def test_trace_status_endpoint_calibration_false() -> None:
    r = client.get("/api/v1/trace/status")
    assert r.status_code == 200
    assert r.json()["data"]["trace_production_calibrated"] is False
