from __future__ import annotations

from app.services.lnurl.audit import LNURLAuditService


def test_lnurl_auth_flow_events_append_to_common_audit_adapter() -> None:
    audit = LNURLAuditService()
    emit = audit.as_event_emitter()

    emit("lnurl_auth_challenge_created", {"challenge_hash": "sha256:c", "auth_domain_hash": "sha256:d", "action": "login"})
    emit(
        "lnurl_auth_callback_success",
        {
            "principal_hash": "hmac-sha256:p",
            "challenge_hash": "sha256:c",
            "auth_domain_hash": "sha256:d",
            "action": "login",
            "verification_strength": "standard",
        },
    )
    emit(
        "lightning_principal_created",
        {"principal_hash": "hmac-sha256:p", "lnurl_key_hash": "hmac-sha256:k", "auth_domain_hash": "sha256:d"},
    )
    emit("lnurl_session_created", {"principal_hash": "hmac-sha256:p", "session_hash": "hmac-sha256:s"})
    emit(
        "lnurl_step_up_approved",
        {"principal_hash": "hmac-sha256:p", "session_fingerprint": "hmac-sha256:s", "intent_hash": "sha256:i"},
    )

    assert audit.memory_chain is not None
    assert [event.reference.event_type for event in audit.memory_chain.events] == [
        "lnurl_auth_challenge_created",
        "lnurl_auth_callback_succeeded",
        "lightning_principal_created",
        "lnurl_auth_session_created",
        "lnurl_auth_step_up_succeeded",
    ]
    assert audit.memory_chain.verify_chain()["valid"] is True
