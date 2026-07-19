from fastapi.testclient import TestClient

from app.main import app


def test_business_lightning_management_api_flow():
    client = TestClient(app)
    created = client.post("/api/v1/business/lightning-domains", json={"normalized_domain": "payregister.bitcoin-bastion.com", "workspace_id_hash": "hmac:workspace", "verification_method": "bastion_managed"})
    assert created.status_code == 200
    domain_id = created.json()["domain_id"]
    address = client.post("/api/v1/business/lightning-addresses", json={"domain_id": domain_id, "local_part": "store-123", "workspace_id_hash": "hmac:workspace", "target_type": "store", "target_id_hash": "hmac:store", "display_label": "Store 123"})
    assert address.status_code == 200
    address_id = address.json()["address_id"]
    activated = client.post(f"/api/v1/business/lightning-addresses/{address_id}/activate")
    assert activated.json()["status"] == "active"
