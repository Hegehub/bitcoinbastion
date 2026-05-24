from fastapi.testclient import TestClient

from app.main import app


def test_security_headers_present() -> None:
    client = TestClient(app)
    r = client.get('/api/v1/public/status')
    assert r.status_code == 200
    for h in ['content-security-policy', 'x-frame-options', 'x-content-type-options', 'referrer-policy', 'permissions-policy', 'cross-origin-opener-policy', 'cross-origin-resource-policy']:
        assert h in {k.lower(): v for k, v in r.headers.items()}


def test_rate_limit_shape() -> None:
    client = TestClient(app)
    # best-effort brute to trigger low public limit
    last = None
    for _ in range(80):
        last = client.get('/api/v1/public/status')
        if last.status_code == 429:
            break
    assert last is not None
    if last.status_code == 429:
        payload = last.json()
        assert payload['error']['code'] == 'rate_limited'
