from fastapi.testclient import TestClient

from app.main import app


def test_openapi_generates_and_has_operation_ids() -> None:
    client = TestClient(app)
    spec = client.get('/openapi.json').json()
    assert 'paths' in spec
    critical = ['/api/v1/public/status', '/api/v1/trace/lite/{address}', '/api/v1/trace/status']
    for path in critical:
        assert path in spec['paths']
        for _, op in spec['paths'][path].items():
            assert op.get('operationId')
