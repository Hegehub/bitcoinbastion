from fastapi.testclient import TestClient

from app.main import app


def test_password_login_is_disabled() -> None:
    response = TestClient(app).post(
        "/api/v1/auth/login",
        json={"username": "legacy", "password": "not-allowed"},
    )
    assert response.status_code in {403, 410}
    assert "access_token" not in response.text


def test_password_register_is_disabled() -> None:
    response = TestClient(app).post(
        "/api/v1/auth/register",
        json={"email": "legacy@example.invalid", "username": "legacy", "password": "not-allowed"},
    )
    assert response.status_code in {403, 410}
    assert "access_token" not in response.text
