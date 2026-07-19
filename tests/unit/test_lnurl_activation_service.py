from __future__ import annotations

import pytest

from app.db.repositories.lnurl_success_action_repository import InMemoryLNURLSuccessActionRepository
from app.domain.lnurl.success_actions import LNURLActivationPurpose, LNURLActivationStatus
from app.services.lnurl.activation_service import ActivationDependencyState, InMemoryActivationStateProvider, LNURLActivationService
from app.services.lnurl.success_action import LNURLSuccessActionConfig, LNURLSuccessActionService


def make_activation_service(ttl_seconds: int = 3600):
    repo = InMemoryLNURLSuccessActionRepository()
    success = LNURLSuccessActionService(
        repository=repo,
        config=LNURLSuccessActionConfig(base_url="https://pay.example.com", allowed_hosts=frozenset({"pay.example.com"}), activation_ttl_seconds=ttl_seconds),
    )
    state = InMemoryActivationStateProvider()
    return LNURLActivationService(success_action_service=success, state_provider=state), state


async def create(service, payment_id="lpay_1", purpose=LNURLActivationPurpose.SUBSCRIPTION_ACTIVATION):
    return await service.create_activation(payment_request_id=payment_id, purpose=purpose, callback_origin="https://pay.example.com/lnurl")


@pytest.mark.anyio
async def test_invoice_issued_remains_payment_pending():
    service, _state = make_activation_service()
    _record, raw = await create(service)
    response = await service.get_activation_status(raw)
    assert response.status == LNURLActivationStatus.PAYMENT_PENDING
    assert response.ready is False


@pytest.mark.anyio
async def test_settled_payment_without_payment_proof_does_not_complete():
    service, state = make_activation_service()
    _record, raw = await create(service)
    state.set_state("lpay_1", ActivationDependencyState(payment_settled=True, payment_proof_exists=False))
    with pytest.raises(ValueError, match="payment_proof_missing"):
        await service.complete_activation(raw, expected_purpose=LNURLActivationPurpose.SUBSCRIPTION_ACTIVATION)


@pytest.mark.anyio
async def test_payment_proof_without_entitlement_is_pending():
    service, state = make_activation_service()
    _record, raw = await create(service)
    state.set_state("lpay_1", ActivationDependencyState(payment_settled=True, payment_proof_exists=True, payment_proof_id="lpp_1"))
    response = await service.get_activation_status(raw)
    assert response.status == LNURLActivationStatus.ENTITLEMENT_PENDING


@pytest.mark.anyio
async def test_settled_payment_plus_entitlement_becomes_ready_and_completes_idempotently():
    service, state = make_activation_service()
    _record, raw = await create(service)
    state.set_state("lpay_1", ActivationDependencyState(payment_settled=True, payment_proof_exists=True, entitlement_active=True, payment_proof_id="lpp_1", entitlement_id="ent_1"))
    ready = await service.get_activation_status(raw)
    assert ready.status == LNURLActivationStatus.READY
    done = await service.complete_activation(raw, expected_purpose=LNURLActivationPurpose.SUBSCRIPTION_ACTIVATION, device_key_fingerprint="sha256:device")
    replay = await service.complete_activation(raw, expected_purpose=LNURLActivationPurpose.SUBSCRIPTION_ACTIVATION, device_key_fingerprint="sha256:device")
    assert done.completed is True
    assert replay.completed is True


@pytest.mark.anyio
async def test_expired_revoked_and_refunded_activation_fail():
    service, state = make_activation_service()
    _record, raw = await create(service)
    state.set_state("lpay_1", ActivationDependencyState(payment_settled=True, payment_proof_exists=True, entitlement_active=True))
    await service.expire_activation(raw)
    with pytest.raises(ValueError, match="activation_expired"):
        await service.complete_activation(raw, expected_purpose=LNURLActivationPurpose.SUBSCRIPTION_ACTIVATION)

    service2, state2 = make_activation_service()
    _record2, raw2 = await create(service2, payment_id="lpay_2")
    state2.set_state("lpay_2", ActivationDependencyState(payment_settled=True, payment_proof_exists=True, entitlement_active=True))
    await service2.revoke_activation(raw2)
    with pytest.raises(ValueError, match="activation_revoked"):
        await service2.complete_activation(raw2, expected_purpose=LNURLActivationPurpose.SUBSCRIPTION_ACTIVATION)

    service3, state3 = make_activation_service()
    _record3, raw3 = await create(service3, payment_id="lpay_3")
    state3.set_state("lpay_3", ActivationDependencyState(payment_refunded=True))
    with pytest.raises(ValueError, match="activation_refunded"):
        await service3.complete_activation(raw3, expected_purpose=LNURLActivationPurpose.SUBSCRIPTION_ACTIVATION)


@pytest.mark.anyio
async def test_duplicate_active_activation_is_prevented():
    service, _state = make_activation_service()
    record1, raw1 = await create(service)
    record2, raw2 = await create(service)
    assert record1.activation_id == record2.activation_id
    assert raw1 != raw2


@pytest.mark.anyio
async def test_raw_activation_token_not_stored_and_opening_does_not_issue_session_or_access_pass():
    service, _state = make_activation_service()
    record, raw = await create(service)
    opened = await service.open_activation(raw)
    assert opened.status in {LNURLActivationStatus.OPENED, LNURLActivationStatus.PAYMENT_PENDING}
    assert raw not in record.activation_reference_hash
    dumped = opened.model_dump_json()
    assert "access_pass" not in dumped.lower()
    assert "session_token" not in dumped.lower()


@pytest.mark.anyio
async def test_entitlement_revocation_blocks_completion():
    service, state = make_activation_service()
    _record, raw = await create(service)
    state.set_state("lpay_1", ActivationDependencyState(payment_settled=True, payment_proof_exists=True, entitlement_active=True, entitlement_revoked=True))
    with pytest.raises(ValueError, match="activation_revoked"):
        await service.complete_activation(raw, expected_purpose=LNURLActivationPurpose.SUBSCRIPTION_ACTIVATION)
