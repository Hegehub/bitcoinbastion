from fastapi.testclient import TestClient

from app.api.dependencies import get_admin_user
from app.main import app


class FakeAdminUser:
    is_admin = True


def test_new_api_groups_exist() -> None:
    app.dependency_overrides[get_admin_user] = lambda: FakeAdminUser()
    client = TestClient(app)
    try:
        assert client.get("/api/v1/admin/status").status_code == 200
        assert client.get("/api/v1/admin/jobs").status_code == 200
        assert client.get("/api/v1/onchain/events").status_code == 200
        assert client.get("/api/v1/entities").status_code == 200
        assert client.post(
            "/api/v1/fees/recommendation",
            json={"mempool_congestion": 0.5, "target_blocks": 6},
        ).status_code == 200
        assert client.get("/metrics").status_code == 200
    finally:
        app.dependency_overrides.clear()
