from fastapi.testclient import TestClient
from app.main import app


def test_timeline_latest_route() -> None:
    c = TestClient(app)
    r = c.get('/api/v1/intelligence/timeline/latest')
    assert r.status_code == 200
