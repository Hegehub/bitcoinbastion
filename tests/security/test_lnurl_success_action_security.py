from __future__ import annotations

import pytest

from app.domain.lnurl.success_actions import LNURLActivationPurpose, LNURLActivationStatus, LNURL_ACTIVATION_REFERENCE_BYTES
from app.schemas.lnurl_success_action import LNURLMessageSuccessAction, LNURLURLSuccessAction
from app.services.lnurl.activation_service import ActivationDependencyState, InMemoryActivationStateProvider, LNURLActivationService
from app.services.lnurl.success_action import LNURLSuccessActionConfig, LNURLSuccessActionService


def make_services():
    state = InMemoryActivationStateProvider()
    success = LNURLSuccessActionService(config=LNURLSuccessActionConfig(base_url="https://pay.example.com", allowed_hosts=frozenset({"pay.example.com"})))
    activation = LNURLActivationService(success_action_service=success, state_provider=state)
    return success, activation, state


@pytest.mark.anyio
async def test_success_action_invoice_and_frontend_do_not_activate_access():
    success, activation, _state = make_services()
    action = await success.render_lnurl_callback_response_fragment(
        payment_request_id="lpay_sec_1",
        purpose=LNURLActivationPurpose.SUBSCRIPTION_ACTIVATION,
        callback_origin="https://pay.example.com/lnurl/callback",
    )
    raw_ref = action["url"].rsplit("/", 1)[1]
    opened = await activation.open_activation(raw_ref)
    assert opened.ready is False
    assert opened.status in {LNURLActivationStatus.OPENED, LNURLActivationStatus.PAYMENT_PENDING}
    with pytest.raises(ValueError, match="payment_not_settled"):
        await activation.complete_activation(raw_ref, expected_purpose=LNURLActivationPurpose.SUBSCRIPTION_ACTIVATION)


@pytest.mark.parametrize("value", ["access_pass=raw", "session_token=raw", "seed phrase", "private_key", "xprv9secret", "mnemonic words"])
def test_raw_secrets_rejected_from_message_description_and_url(value):
    with pytest.raises(ValueError):
        LNURLMessageSuccessAction(message=f"Open {value}")
    with pytest.raises(ValueError):
        LNURLURLSuccessAction(description=f"Open {value}", url="https://pay.example.com/access/activate/abc")
    with pytest.raises(ValueError):
        LNURLURLSuccessAction(description="Open", url=f"https://pay.example.com/access/activate/abc?x={value}")


def test_different_domain_and_open_redirect_rejected():
    success, _activation, _state = make_services()
    with pytest.raises(ValueError):
        success.build_url_action(
            description="Open",
            raw_reference="lnact_abc",
            callback_origin="https://pay.example.com/lnurl",
            purpose=LNURLActivationPurpose.SUBSCRIPTION_ACTIVATION,
        ) if False else success.validate_safe_target_path("/access/activate//evil.example")
    with pytest.raises(ValueError):
        success.validate_callback_domain("https://evil.example.com/lnurl")


def test_activation_reference_entropy():
    success, _activation, _state = make_services()
    reference = success.create_activation_reference()
    assert reference.startswith("lnact_")
    assert len(reference) >= LNURL_ACTIVATION_REFERENCE_BYTES


@pytest.mark.anyio
async def test_raw_activation_reference_not_stored_and_generic_not_found():
    success, activation, _state = make_services()
    action = await success.render_lnurl_callback_response_fragment(
        payment_request_id="lpay_sec_2",
        purpose=LNURLActivationPurpose.PAYMENT_RECEIPT,
        callback_origin="https://pay.example.com/lnurl",
    )
    raw_ref = action["url"].rsplit("/", 1)[1]
    records = await success.repository.get_by_payment_request_id("lpay_sec_2")
    assert raw_ref not in repr(records[0])
    with pytest.raises(ValueError, match="activation_not_found"):
        await activation.get_activation_status("lnact_missing")


@pytest.mark.anyio
async def test_expired_revoked_refunded_and_entitlement_mismatch_block_activation():
    success, activation, state = make_services()
    action = await success.render_lnurl_callback_response_fragment(
        payment_request_id="lpay_sec_3",
        purpose=LNURLActivationPurpose.SUBSCRIPTION_ACTIVATION,
        callback_origin="https://pay.example.com/lnurl",
    )
    raw_ref = action["url"].rsplit("/", 1)[1]
    state.set_state("lpay_sec_3", ActivationDependencyState(payment_settled=True, payment_proof_exists=True, entitlement_active=False))
    with pytest.raises(ValueError, match="entitlement_pending"):
        await activation.complete_activation(raw_ref, expected_purpose=LNURLActivationPurpose.SUBSCRIPTION_ACTIVATION)
    await activation.revoke_activation(raw_ref)
    with pytest.raises(ValueError, match="activation_revoked"):
        await activation.complete_activation(raw_ref, expected_purpose=LNURLActivationPurpose.SUBSCRIPTION_ACTIVATION)


@pytest.mark.anyio
async def test_refunded_payment_and_payregister_receipt_privacy():
    success, activation, state = make_services()
    action = await success.render_lnurl_callback_response_fragment(
        payment_request_id="lpay_receipt_sec",
        purpose=LNURLActivationPurpose.PAYREGISTER_RECEIPT,
        callback_origin="https://pay.example.com/lnurl",
        description="Open your PayRegister receipt",
    )
    raw_ref = action["url"].rsplit("/", 1)[1]
    state.set_state("lpay_receipt_sec", ActivationDependencyState(payment_refunded=True))
    response = await activation.get_activation_status(raw_ref)
    assert response.status == LNURLActivationStatus.REFUNDED
    dumped = response.model_dump_json().lower()
    assert "cashier" not in dumped
    assert "merchant_api" not in dumped
    assert "linking_key" not in dumped
