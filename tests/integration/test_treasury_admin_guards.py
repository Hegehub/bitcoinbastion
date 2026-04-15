from fastapi.testclient import TestClient

from app.main import app


def test_treasury_pending_approvals_requires_admin_auth() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/treasury/requests/pending-approvals")

    assert response.status_code in {401, 403}


def test_treasury_approve_requires_admin_auth() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/v1/treasury/requests/1/approve",
        json={"policy_name": "default", "wallet_health_score": 90, "note": "approve"},
    )

    assert response.status_code in {401, 403}


def test_treasury_reject_requires_admin_auth() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/v1/treasury/requests/1/reject",
        json={"note": "reject"},
    )

    assert response.status_code in {401, 403}
