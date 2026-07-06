from __future__ import annotations

import logging

import pytest

from app.schemas.access_intent import HumanIntentAction, HumanIntentCreateRequest
from app.services.access.human_intent import CRITICAL_HUMAN_INTENT_ACTIONS, HumanIntentError
from tests.unit.test_human_intent_signature import _context, _request, _service_with_device


@pytest.mark.parametrize("action", sorted(CRITICAL_HUMAN_INTENT_ACTIONS))
def test_critical_actions_fail_without_human_intent(action: str) -> None:
    service, _private, _device_fp = _service_with_device()
    with pytest.raises(HumanIntentError, match="human_intent_required"):
        service.require_valid_intent(intent_id=None, action=action)


def test_signed_intent_cannot_authorize_other_action_origin_or_scope() -> None:
    service, private, device_fp = _service_with_device()
    response = service.create_intent(_context(device_fp), _request(HumanIntentAction.CREATE_API_KEY))
    from app.services.access.crypto.signatures import Ed25519SignatureSuite

    signature = Ed25519SignatureSuite().sign(response.canonical_manifest_hash, "human_intent", "device", private).signature
    assert service.verify_intent_signature(intent_id=response.intent_id, signature=signature, signature_alg="ed25519", device_key_fingerprint=device_fp).valid
    with pytest.raises(HumanIntentError, match="human_intent_action_mismatch"):
        service.require_valid_intent(intent_id=response.intent_id, action="create_delegated_pass")
    with pytest.raises(HumanIntentError, match="human_intent_origin_mismatch"):
        service.require_valid_intent(intent_id=response.intent_id, action="create_api_key", origin="https://evil.example")
    with pytest.raises(HumanIntentError, match="human_intent_scope_mismatch"):
        service.require_valid_intent(intent_id=response.intent_id, action="create_api_key", requested_scopes=["market:intelligence:read", "trace:standard:read"])


def test_verified_intent_cannot_be_replayed() -> None:
    service, private, device_fp = _service_with_device()
    response = service.create_intent(_context(device_fp), _request())
    from app.services.access.crypto.signatures import Ed25519SignatureSuite

    signature = Ed25519SignatureSuite().sign(response.canonical_manifest_hash, "human_intent", "device", private).signature
    assert service.verify_intent_signature(intent_id=response.intent_id, signature=signature, signature_alg="ed25519", device_key_fingerprint=device_fp).valid
    service.mark_intent_used(response.intent_id)
    with pytest.raises(HumanIntentError, match="human_intent_replay"):
        service.mark_intent_used(response.intent_id)


def test_logs_do_not_contain_raw_sensitive_values(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.INFO)
    service, _private, device_fp = _service_with_device()
    request = HumanIntentCreateRequest(
        action=HumanIntentAction.CREATE_DELEGATED_PASS,
        requested_scopes=["market:intelligence:read"],
        cannot_access=["treasury:read"],
        target_resource_type="delegated_pass",
        origin="https://app.example",
        human_summary="Delegate read-only market access",
        consequences=["Temporary read-only access"],
    )
    service.create_intent(_context(device_fp), request)
    log_text = caplog.text
    assert "raw_pass" not in log_text
    assert "session_token" not in log_text
    assert "recovery_phrase" not in log_text
    assert "signature" not in log_text
