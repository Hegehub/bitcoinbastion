from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.domain.access.errors import AccessAuditError
from app.services.lnurl.audit import (
    AuditOutcome,
    LNURLAuditService,
    LNURLAuthAuditEventType,
    build_lnurl_canonical_audit_event,
    compute_lnurl_audit_hash,
    normalize_lnurl_audit_event_type,
    sanitize_lnurl_audit_metadata,
)

FIXED = datetime(2026, 7, 17, 12, 0, tzinfo=UTC)


def service() -> LNURLAuditService:
    return LNURLAuditService(clock=lambda: FIXED)


def test_all_required_event_types_are_defined_and_stable() -> None:
    required = {
        "lnurl_auth_challenge_created",
        "lnurl_auth_challenge_expired",
        "lnurl_auth_challenge_cancelled",
        "lnurl_auth_challenge_consumed",
        "lnurl_auth_challenge_rejected",
        "lnurl_auth_callback_received",
        "lnurl_auth_callback_succeeded",
        "lnurl_auth_callback_failed",
        "lnurl_auth_signature_invalid",
        "lnurl_auth_key_invalid",
        "lnurl_auth_action_invalid",
        "lnurl_auth_domain_mismatch",
        "lnurl_auth_k1_unknown",
        "lnurl_auth_k1_expired",
        "lnurl_auth_k1_reused",
        "lnurl_auth_replay_rejected",
        "lightning_principal_created",
        "lightning_principal_verified",
        "lightning_principal_linked",
        "lightning_principal_link_failed",
        "lightning_principal_suspended",
        "lightning_principal_revoked",
        "lnurl_device_binding_requested",
        "lnurl_device_bound",
        "lnurl_device_binding_failed",
        "lnurl_device_revoked",
        "lnurl_auth_session_requested",
        "lnurl_auth_session_created",
        "lnurl_auth_session_denied",
        "lnurl_auth_session_expired",
        "lnurl_auth_session_revoked",
        "lnurl_auth_session_frozen",
        "lnurl_auth_step_up_requested",
        "lnurl_auth_step_up_succeeded",
        "lnurl_auth_step_up_failed",
        "lnurl_auth_step_up_expired",
        "lnurl_auth_step_up_replayed",
        "lnurl_auth_step_up_policy_denied",
        "lnurl_auth_policy_allowed",
        "lnurl_auth_policy_denied",
        "lnurl_auth_rate_limited",
        "lnurl_auth_risk_escalated",
        "lnurl_auth_lockdown_triggered",
        "lnurl_auth_compatibility_downgrade_detected",
    }

    assert required <= {event.value for event in LNURLAuthAuditEventType}


def test_unsupported_event_type_rejected() -> None:
    with pytest.raises(AccessAuditError):
        normalize_lnurl_audit_event_type("lnurl_auth_totally_new_event")


def test_canonical_hash_is_stable_under_field_ordering() -> None:
    first = build_lnurl_canonical_audit_event(
        event_type="lnurl_auth_callback_succeeded",
        outcome="success",
        severity="info",
        principal_hash="hmac-sha256:principal",
        challenge_hash="sha256:challenge",
        device_key_fingerprint=None,
        session_hash=None,
        action="login",
        bastion_action=None,
        auth_domain_hash="sha256:domain",
        verification_strength="standard",
        policy_hash="sha256:policy",
        policy_epoch=1,
        policy_decision="allow",
        crypto_epoch=1,
        request_correlation_id="corr_1",
        reason_code=None,
        revocation=None,
        metadata={"b": 2, "a": 1},
        occurred_at="2026-07-17T12:00:00Z",
    )
    second = {**first, "metadata": {"a": 1, "b": 2}}

    assert compute_lnurl_audit_hash(None, first) == compute_lnurl_audit_hash(None, second)


def test_payload_mutation_changes_hash() -> None:
    payload = build_lnurl_canonical_audit_event(
        event_type="lnurl_auth_session_created",
        outcome="success",
        severity="info",
        principal_hash="hmac-sha256:principal",
        challenge_hash="sha256:challenge",
        device_key_fingerprint="sha256:device",
        session_hash="hmac-sha256:session",
        action="login",
        bastion_action=None,
        auth_domain_hash="sha256:domain",
        verification_strength="standard",
        policy_hash="sha256:policy",
        policy_epoch=1,
        policy_decision="allow",
        crypto_epoch=1,
        request_correlation_id=None,
        reason_code=None,
        revocation=None,
        metadata={"approved_scopes": ["metrics:read"]},
        occurred_at="2026-07-17T12:00:00Z",
    )
    changed = {**payload, "auth": {**payload["auth"], "action": "register"}}

    assert compute_lnurl_audit_hash(None, payload) != compute_lnurl_audit_hash(None, changed)


def test_in_memory_chain_verifies_and_detects_mutation() -> None:
    audit = service()
    audit.record_lnurl_auth_event(
        event_type=LNURLAuthAuditEventType.LNURL_AUTH_CHALLENGE_CREATED,
        outcome=AuditOutcome.SUCCESS,
        challenge_hash="sha256:challenge1",
        auth_domain_hash="sha256:domain",
        action="login",
    )
    audit.record_lnurl_auth_event(
        event_type=LNURLAuthAuditEventType.LNURL_AUTH_CALLBACK_SUCCEEDED,
        outcome=AuditOutcome.SUCCESS,
        principal_hash="hmac-sha256:principal",
        challenge_hash="sha256:challenge1",
        auth_domain_hash="sha256:domain",
        action="login",
    )

    assert audit.memory_chain is not None
    assert audit.memory_chain.verify_chain()["valid"] is True
    tampered = list(audit.memory_chain.events)
    tampered[1] = type(tampered[1])(tampered[1].reference, {**tampered[1].canonical_event, "outcome": "failure"})
    assert audit.memory_chain.verify_chain(tampered)["valid"] is False


def test_safe_hash_fields_are_accepted() -> None:
    assert sanitize_lnurl_audit_metadata(
        {
            "k1_hash": "hmac-sha256:k1",
            "challenge_hash": "sha256:challenge",
            "signature_hash": "sha256:sig",
            "linking_key_hash": "hmac-sha256:key",
            "principal_hash": "hmac-sha256:principal",
            "session_hash": "hmac-sha256:session",
            "device_key_fingerprint": "sha256:device",
        }
    )


def test_duplicate_success_event_is_idempotent() -> None:
    audit = service()
    first = audit.record_lnurl_auth_event(
        event_type="lnurl_auth_callback_succeeded",
        outcome="success",
        principal_hash="hmac-sha256:principal",
        challenge_hash="sha256:challenge",
        auth_domain_hash="sha256:domain",
        action="login",
    )
    second = audit.record_lnurl_auth_event(
        event_type="lnurl_auth_callback_succeeded",
        outcome="success",
        principal_hash="hmac-sha256:principal",
        challenge_hash="sha256:challenge",
        auth_domain_hash="sha256:domain",
        action="login",
    )

    assert second == first
    assert audit.memory_chain is not None
    assert len(audit.memory_chain.events) == 1


def test_service_hook_alias_maps_existing_lnurl_events() -> None:
    audit = service()
    ref = audit.as_event_emitter()("lnurl_session_created", {"principal_hash": "hmac-sha256:p", "session_hash": "hmac-sha256:s"})

    assert ref.event_type == "lnurl_auth_session_created"
