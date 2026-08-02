from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi.testclient import TestClient

from app.api.v1.wallet_auth import get_wallet_auth_backend
from app.api.wallet_auth_dependencies import require_fresh_wallet_step_up, require_wallet_policy
from app.main import app


class FakeBackend:
    policy_calls = 0

    async def register(self, request: Any, *, idempotency_key: str | None):
        return {"principal": {"principal_id": "wpr_public123", "principal_type": "bitcoin_wallet_principal", "status": "active", "network": "bitcoin-mainnet", "proof_method": "bip322", "verification_strength": "standard", "created_at": datetime.now(UTC).isoformat()}, "device": {"device_id": "wdev_public123", "device_class": "desktop_vault", "status": "active", "created_at": datetime.now(UTC).isoformat()}, "next_action": "create_session", "authentication_grant": "wag_once"}

    async def login(self, request: Any):
        return {"authentication_grant": "wag_once", "expires_at": datetime.now(UTC) + timedelta(minutes=2), "next_action": "create_session"}

    async def create_session(self, request: Any, *, idempotency_key: str | None):
        return {"session_token": "sess_returned_once", "session_id": "wsess_public123", "principal_id": "wpr_public123", "device_id": "wdev_public123", "expires_at": (datetime.now(UTC) + timedelta(minutes=15)).isoformat(), "scopes": request.requested_scopes, "plan": "lite_pass", "proof_of_possession_required": True}

    async def me(self, context: Any):
        self.policy_calls += 1
        return {"principal_id": "wpr_public123", "principal_type": "bitcoin_wallet_principal", "status": "active", "verification_strength": "standard"}

    def __getattr__(self, name: str):
        async def method(*args: Any, **kwargs: Any):
            if name in {"devices", "wallets"}:
                return {name: []}
            return {"status": "ok"}
        return method


async def allow_policy() -> dict[str, str]:
    return {"principal_id": "wpr_public123"}


def test_register_login_session_and_protected_me_flow():
    backend = FakeBackend()
    app.dependency_overrides[get_wallet_auth_backend] = lambda: backend
    app.dependency_overrides[require_wallet_policy] = allow_policy
    app.dependency_overrides[require_fresh_wallet_step_up] = allow_policy
    client = TestClient(app)
    try:
        registration = client.post("/api/v1/wallet-auth/register", json={"challenge_id": "wch_test", "proof_type": "bip322", "wallet_identifier": "bc1qfictional", "signature": "fictional-signature", "device_key_fingerprint": "sha256:" + "1" * 64, "device_class": "desktop_vault", "origin": "https://bitcoin-bastion.com", "network": "bitcoin-mainnet"})
        assert registration.status_code == 200
        assert "wallet_identifier" not in registration.text
        login = client.post("/api/v1/wallet-auth/login", json={"challenge_id": "wch_test", "proof_type": "bip322", "wallet_identifier": "bc1qfictional", "signature": "fictional-signature", "device_key_fingerprint": "sha256:" + "1" * 64, "origin": "https://bitcoin-bastion.com", "network": "bitcoin-mainnet"})
        assert login.status_code == 200
        session = client.post("/api/v1/wallet-auth/sessions", json={"authentication_grant": "wag_once", "device_public_key": "fictional-public-key", "session_public_key": "fictional-session-key", "requested_scopes": ["quotes:read"]})
        assert session.json()["proof_of_possession_required"] is True
        assert client.get("/api/v1/wallet-auth/me").status_code == 200
        assert backend.policy_calls == 1
    finally:
        app.dependency_overrides.clear()


def test_recovery_secret_inputs_are_rejected_without_echo():
    app.dependency_overrides[get_wallet_auth_backend] = lambda: FakeBackend()
    response = TestClient(app).post("/api/v1/wallet-auth/recovery/wrec_12345678/factor", json={"factor_type": "recovery_file", "proof": {"mnemonic": "abandon abandon secret"}})
    app.dependency_overrides.clear()
    assert response.status_code == 422
    assert "abandon" not in response.text
