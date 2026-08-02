from typing import Any

from fastapi.testclient import TestClient

from app.api.v1.lnurl import get_lnurl_api_backend
from app.api.wallet_auth_dependencies import require_wallet_policy
from app.main import app


class FakeLNURLBackend:
    def __init__(self) -> None:
        self.auth_callbacks = 0
        self.withdraw_callbacks = 0
        self.entitlements = 0

    async def create_auth_challenge(self, request: Any):
        return {"challenge_id": "lac_test123", "lnurl": "LNURL1FICTIONAL", "qr_payload": "LNURL1FICTIONAL", "action": request.action.value, "expires_at": "2026-08-02T00:05:00Z", "auth_domain": "auth.bitcoin-bastion.com", "warning": "LNURL-auth does not grant access."}

    async def auth_callback(self, **kwargs: Any):
        self.auth_callbacks += 1
        return {"status": "OK"} if self.auth_callbacks == 1 else {"status": "ERROR"}

    async def create_auth_session(self, request: Any):
        return {"session_token": "sess_once", "proof_of_possession_required": True, "auth_attempt_id": request.auth_attempt_id}

    async def create_auth_step_up(self, context: Any, request: Any):
        return {"step_up_id": "lnstep_test", "action": request.action, "single_use": True}

    async def create_subscription(self, request: Any):
        return {"payment_id": "lnpay_test", "tag": "payRequest", "callback": "https://bitcoin-bastion.com/v1/lnurl/pay/callback/lnpay_test", "minSendable": 1000, "maxSendable": 1000, "metadata": "[[\"text/plain\",\"Fictional pass\"]]"}

    async def pay_callback(self, payment_id: str, **kwargs: Any):
        return {"pr": "lnbc1fictional", "routes": [], "verify": f"https://bitcoin-bastion.com/v1/lnurl/pay/verify/{payment_id}"}

    async def verify_payment(self, payment_id: str):
        return {"status": "pending", "settled": False, "payment_id": payment_id, "entitlement_issued": False}

    async def create_withdraw(self, context: Any, request: Any):
        return {"withdraw_id": "lnw_test123", "lnurl": "LNURL1WITHDRAW", "policy_approved": True, "amount_msat": request.amount_msat}

    async def withdraw_callback(self, withdraw_id: str, **kwargs: Any):
        self.withdraw_callbacks += 1
        return {"status": "OK"} if self.withdraw_callbacks == 1 else {"status": "ERROR"}


async def policy_context() -> dict[str, str]:
    return {"principal_id": "lightning-product-pseudonym"}


def test_lnurl_auth_pay_verify_withdraw_and_protocol_shapes():
    backend = FakeLNURLBackend()
    app.dependency_overrides[get_lnurl_api_backend] = lambda: backend
    app.dependency_overrides[require_wallet_policy] = policy_context
    client = TestClient(app)
    try:
        challenge = client.post("/v1/lnurl/auth/challenges", json={"action": "login", "origin": "https://bitcoin-bastion.com", "requested_scopes": []})
        assert challenge.status_code == 200 and challenge.json()["error"] is None
        assert "k1" not in challenge.request.content.decode()  # caller cannot supply k1
        callback_url = "/v1/lnurl/auth/callback?k1=" + "01" * 32 + "&key=02" + "02" * 32 + "&sig=3001"
        first = client.get(callback_url)
        second = client.get(callback_url)
        assert first.json() == {"status": "OK"}
        assert second.json()["status"] == "ERROR"
        assert first.headers["access-control-allow-origin"] == "*"
        session = client.post("/v1/lnurl/auth/sessions", json={"auth_attempt_id": "laa_test", "device_public_key": "device-key", "device_key_fingerprint": "sha256:" + "1" * 64, "session_public_key": "session-key", "requested_scopes": []})
        assert session.json()["data"]["proof_of_possession_required"] is True
        pay = client.post("/v1/lnurl/pay/subscriptions", json={"plan_code": "pro_pass"})
        assert pay.json()["data"]["tag"] == "payRequest"
        invoice = client.get("/v1/lnurl/pay/callback/lnpay_test?amount=1000")
        assert "pr" in invoice.json() and "entitlement" not in invoice.text
        verify = client.get("/v1/lnurl/pay/verify/lnpay_test")
        assert verify.json()["settled"] is False and backend.entitlements == 0
        withdraw = client.post("/v1/lnurl/withdraw/requests", json={"amount_msat": 1000, "purpose": "subscription_refund", "description": "Fictional refund"})
        assert withdraw.json()["data"]["policy_approved"] is True
    finally:
        app.dependency_overrides.clear()


def test_invalid_plan_and_secret_input_fail_without_echo():
    app.dependency_overrides[get_lnurl_api_backend] = lambda: FakeLNURLBackend()
    client = TestClient(app)
    invalid = client.post("/v1/lnurl/pay/subscriptions", json={"plan_code": "base_pass"})
    secret = client.post("/v1/lnurl/auth/challenges", json={"action": "login", "origin": "https://bitcoin-bastion.com", "risk_context": {"private_key": "do-not-echo"}})
    app.dependency_overrides.clear()
    assert invalid.status_code == 422
    assert secret.status_code == 422 and "do-not-echo" not in secret.text
