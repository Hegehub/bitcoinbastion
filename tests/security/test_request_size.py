from fastapi.testclient import TestClient

from app.main import app


def test_oversized_body_rejected() -> None:
    client = TestClient(app)
    huge = {"addresses": ["bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh"] * 20000}
    r = client.post("/api/v1/trace/business/batch", json=huge)
    assert r.status_code in {400, 413}
