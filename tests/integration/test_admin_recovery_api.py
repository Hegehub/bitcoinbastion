from fastapi.testclient import TestClient

from app.api.dependencies import get_admin_user
from app.main import app


class FakeAdminUser:
    is_admin = True


def test_admin_recovery_check_includes_hotspots_and_drills() -> None:
    app.dependency_overrides[get_admin_user] = lambda: FakeAdminUser()
    client = TestClient(app)
    try:
        response = client.get("/api/v1/admin/jobs/recovery-check")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    data = payload["data"]
    assert "hotspots" in data
    assert "drills" in data
    assert isinstance(data["hotspots"], list)
    assert isinstance(data["drills"], list)
    if data["drills"]:
        first = data["drills"][0]
        assert "automation_ready" in first
        assert "run_within_hours" in first
