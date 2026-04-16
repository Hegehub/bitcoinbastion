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
        assert client.get("/api/v1/admin/jobs/recovery-check").status_code == 200
        assert client.get("/api/v1/admin/audit-logs").status_code == 200
        assert client.get("/api/v1/onchain/events").status_code == 200
        assert client.get("/api/v1/entities").status_code == 200
        assert client.post("/api/v1/entities/provenance/refresh").status_code == 200
        assert client.post(
            "/api/v1/fees/recommendation",
            json={"mempool_congestion": 0.5, "target_blocks": 6},
        ).status_code == 200
        assert client.post(
            "/api/v1/policy/check",
            json={"policy_name": "default", "wallet_health_score": 82, "transaction_amount_sats": 250000},
        ).status_code == 200
        assert client.get("/api/v1/policy/executions").status_code == 200
        assert client.get("/api/v1/policy/catalog").status_code == 200
        assert client.post(
            "/api/v1/policy/catalog",
            json={
                "name": "ops_strict",
                "description": "Strict policy profile",
                "min_wallet_health_score": 85,
                "max_single_tx_sats": 700000,
            },
        ).status_code == 200
        assert client.post(
            "/api/v1/policy/catalog",
            json={
                "name": "ops_strict",
                "description": "Tightened without governance note",
                "min_wallet_health_score": 99,
                "max_single_tx_sats": 100000,
            },
        ).status_code in {200, 400}
        assert client.post(
            "/api/v1/policy/catalog/compare",
            json={
                "baseline_policy_name": "default",
                "candidate_policy_name": "ops_strict",
            },
        ).status_code == 200
        assert client.post(
            "/api/v1/policy/simulate",
            json={
                "baseline_policy_name": "default",
                "candidate_policy_name": "ops_strict",
                "wallet_health_score": 82,
                "transaction_amount_sats": 250000,
                "required_approvals": 1,
            },
        ).status_code == 200
        assert client.post(
            "/api/v1/privacy/assess",
            json={"reused_addresses": 2, "known_kyc_exposure": False, "utxo_fragmentation_score": 0.2},
        ).status_code == 200
        assert client.get("/api/v1/education/snippets").status_code == 200
        assert client.get("/api/v1/observability/snapshot").status_code == 200
        assert client.get("/api/v1/citadel/overview").status_code == 200
        assert client.get("/api/v1/citadel/assessment").status_code == 200
        assert client.get("/api/v1/citadel/dependencies").status_code == 200
        assert client.get("/api/v1/citadel/recovery").status_code == 200
        assert client.post("/api/v1/citadel/simulations", json={"owner_id": 9, "scenario_code": "loss_signer"}).status_code == 200
        assert client.get("/api/v1/citadel/simulations").status_code == 200
        assert client.get("/api/v1/citadel/inheritance").status_code == 200
        assert client.get("/api/v1/citadel/repair-plan").status_code == 200
        assert client.get("/api/v1/citadel/policy-checks").status_code == 200
        assert client.post("/api/v1/citadel/recalculate", json={"owner_type": "user", "owner_id": 9}).status_code == 200
        assert client.get("/api/v1/signals/999999/explanation").status_code in {404, 503}
        assert client.get("/api/v1/signals/999999/recommendations").status_code in {404, 503}
        assert client.post("/api/v1/news/sources/reputation/refresh").status_code == 200
        assert client.get("/api/v1/news/sources/reputation").status_code == 200
        assert client.get("/metrics").status_code == 200
    finally:
        app.dependency_overrides.clear()
