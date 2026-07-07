from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_business_profile_endpoint() -> None:
    r = client.get("/api/v1/trace/business/profile")
    assert r.status_code == 200
    assert r.json()["data"]["tier"] == "BUSINESS"


def test_business_batch_endpoint() -> None:
    r = client.post(
        "/api/v1/trace/business/batch",
        json={"addresses": ["bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kg3g4ty"], "batch_label": "b1"},
    )
    assert r.status_code == 200
    assert r.json()["data"]["total_addresses"] == 1


def test_business_policy_profiles_endpoint() -> None:
    r = client.get("/api/v1/trace/business/policy-profiles")
    assert r.status_code == 200
    assert len(r.json()["data"]) >= 1


def test_business_batch_rejects_sensitive_input_without_secret_echo() -> None:
    secret_like = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"
    r = client.post(
        "/api/v1/trace/business/batch", json={"addresses": [secret_like], "batch_label": "s1"}
    )
    assert r.status_code == 200
    item = r.json()["data"]["reports"][0]
    assert item["status"] == "rejected"
    assert item["rejection_reason"] == "sensitive_wallet_material_not_accepted"
    assert "abandon" not in item["address"]
