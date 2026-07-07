from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_enterprise_profile_endpoint() -> None:
    r = client.get("/api/v1/trace/enterprise/profile")
    assert r.status_code == 200
    assert r.json()["data"]["tier"] == "ENTERPRISE"


def test_enterprise_rbac_roles_endpoint() -> None:
    r = client.get("/api/v1/trace/enterprise/rbac/roles")
    assert r.status_code == 200
    assert "OWNER" in r.json()["data"]


def test_enterprise_evidence_access_endpoint() -> None:
    r = client.post(
        "/api/v1/trace/enterprise/evidence-access/evaluate",
        json={"evidence_ref": "ev-1", "requester_role": "READ_ONLY", "purpose": "audit"},
    )
    assert r.status_code == 200
    assert r.json()["data"]["decision"] == "REDACT"


def test_enterprise_proof_packet_has_required_flags() -> None:
    analysis = client.get("/api/v1/trace/address/1BoatSLRHtKNngkdXEeobR76b53LETtpyT")
    report_id = analysis.json()["data"]["id"]
    r = client.post(f"/api/v1/trace/enterprise/proof-packet?report_id={report_id}")
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["advisory_not_legal_verdict"] is True
    assert data["not_consensus_proof"] is True
    assert data["no_custody"] is True
    assert data["not_payment_authorization"] is True
