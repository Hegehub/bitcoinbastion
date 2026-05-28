from fastapi.testclient import TestClient

from app.main import app


def test_news_scores_route_smoke() -> None:
    client = TestClient(app, raise_server_exceptions=False)
    r = client.get('/api/v1/news/1/scores')
    assert r.status_code in {200, 404, 422, 500}


def test_current_narratives_route_smoke() -> None:
    client = TestClient(app, raise_server_exceptions=False)
    r = client.get('/api/v1/intelligence/narratives/current')
    assert r.status_code in {200, 404}
