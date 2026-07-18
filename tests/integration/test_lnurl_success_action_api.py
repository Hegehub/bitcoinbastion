from __future__ import annotations

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.api.v1.lnurl_activation import get_lnurl_activation_service, router
from app.domain.lnurl.success_actions import LNURLActivationPurpose, LNURLActivationStatus, LNURLSuccessActionType
from app.services.lnurl.activation_service import ActivationDependencyState, InMemoryActivationStateProvider, LNURLActivationService
from app.services.lnurl.success_action import LNURLSuccessActionConfig, LNURLSuccessActionService


def make_app():
    state = InMemoryActivationStateProvider()
    success = LNURLSuccessActionService(config=LNURLSuccessActionConfig(base_url="https://pay.example.com", allowed_hosts=frozenset({"pay.example.com"})))
    service = LNURLActivationService(success_action_service=success, state_provider=state)
    app = FastAPI()
    app.include_router(router, prefix="/v1")
    app.dependency_overrides[get_lnurl_activation_service] = lambda: service
    return app, success, service, state


@pytest.mark.anyio
async def test_url_success_action_activation_api_flow():
    app, success, _service, state = make_app()
    action = await success.render_lnurl_callback_response_fragment(
        payment_request_id="lpay_api_1",
        purpose=LNURLActivationPurpose.SUBSCRIPTION_ACTIVATION,
        callback_origin="https://pay.example.com/lnurl/callback",
        action_type=LNURLSuccessActionType.URL,
    )
    assert action["url"].startswith("https://pay.example.com/access/activate/")
    raw_ref = action["url"].rsplit("/", 1)[1]
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        pending = await client.get(f"/v1/lnurl/activations/{raw_ref}")
        assert pending.status_code == 200
        assert pending.json()["status"] == LNURLActivationStatus.PAYMENT_PENDING.value

        state.set_state("lpay_api_1", ActivationDependencyState(payment_settled=True, payment_proof_exists=True, entitlement_active=True, payment_proof_id="lpp_api", entitlement_id="ent_api"))
        ready = await client.get(f"/v1/lnurl/activations/{raw_ref}")
        assert ready.json()["status"] == LNURLActivationStatus.READY.value
        completed = await client.post(
            f"/v1/lnurl/activations/{raw_ref}/complete",
            json={"expected_purpose": LNURLActivationPurpose.SUBSCRIPTION_ACTIVATION.value, "device_key_fingerprint": "sha256:device"},
        )
        replay = await client.post(
            f"/v1/lnurl/activations/{raw_ref}/complete",
            json={"expected_purpose": LNURLActivationPurpose.SUBSCRIPTION_ACTIVATION.value, "device_key_fingerprint": "sha256:device"},
        )
        assert completed.status_code == 200
        assert completed.json()["completed"] is True
        assert replay.json()["completed"] is True


@pytest.mark.anyio
async def test_message_success_action_flow():
    _app, success, _service, _state = make_app()
    action = await success.render_lnurl_callback_response_fragment(
        payment_request_id="lpay_message",
        purpose=LNURLActivationPurpose.PAYMENT_RECEIPT,
        callback_origin="https://pay.example.com/lnurl/callback",
        action_type=LNURLSuccessActionType.MESSAGE,
        message="Payment complete. Receipt is available in Bastion.",
    )
    assert action == {"tag": "message", "message": "Payment complete. Receipt is available in Bastion."}


@pytest.mark.anyio
async def test_payregister_receipt_and_refund_flow():
    app, success, service, state = make_app()
    action = await success.render_lnurl_callback_response_fragment(
        payment_request_id="lpay_receipt",
        purpose=LNURLActivationPurpose.PAYREGISTER_RECEIPT,
        callback_origin="https://pay.example.com/lnurl/callback",
        action_type=LNURLSuccessActionType.URL,
        description="Open your PayRegister receipt",
    )
    assert "/payregister/receipts/" in action["url"]
    raw_ref = action["url"].rsplit("/", 1)[1]
    state.set_state("lpay_receipt", ActivationDependencyState(payment_settled=True, payment_proof_exists=True))
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        receipt = await client.get(f"/v1/lnurl/receipts/{raw_ref}")
        assert receipt.status_code == 200
        assert receipt.json()["ready"] is True
        assert receipt.json()["receipt_reference"].startswith("sha256:")
    await service.handle_payment_refund("lpay_receipt")
    refunded = await service.get_activation_status(raw_ref)
    assert refunded.status == LNURLActivationStatus.REFUNDED


@pytest.mark.anyio
async def test_invalid_domain_and_duplicate_callback_retry():
    _app, success, _service, _state = make_app()
    with pytest.raises(ValueError, match="success_action_domain_mismatch"):
        await success.render_lnurl_callback_response_fragment(
            payment_request_id="lpay_bad",
            purpose=LNURLActivationPurpose.SUBSCRIPTION_ACTIVATION,
            callback_origin="https://evil.example.com/lnurl/callback",
        )
    first = await success.create_activation_record(
        payment_request_id="lpay_dup",
        purpose=LNURLActivationPurpose.SUBSCRIPTION_ACTIVATION,
        callback_origin="https://pay.example.com/lnurl/callback",
    )
    second = await success.create_activation_record(
        payment_request_id="lpay_dup",
        purpose=LNURLActivationPurpose.SUBSCRIPTION_ACTIVATION,
        callback_origin="https://pay.example.com/lnurl/callback",
    )
    assert first[0].activation_id == second[0].activation_id
    assert second[1] == ""
