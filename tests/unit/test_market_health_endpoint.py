from fastapi.testclient import TestClient
from app.main import app


def test_market_health_route() -> None:
    c = TestClient(app)
    r = c.get('/api/v1/market/health')
    assert r.status_code == 200
