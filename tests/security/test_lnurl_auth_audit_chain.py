from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.domain.access.errors import AccessAuditError
from app.services.lnurl.audit import LNURLAuditService

FIXED = datetime(2026, 7, 17, 12, 0, tzinfo=UTC)


def make_service() -> LNURLAuditService:
    return LNURLAuditService(clock=lambda: FIXED)


def populate(audit: LNURLAuditService) -> None:
    audit.record_lnurl_auth_event(
        event_type="lnurl_auth_challenge_created",
        outcome="success",
        challenge_hash="sha256:c1",
        auth_domain_hash="sha256:d",
    )
    audit.record_lnurl_auth_event(
        event_type="lnurl_auth_callback_succeeded",
        outcome="success",
        principal_hash="hmac-sha256:p",
        challenge_hash="sha256:c1",
        auth_domain_hash="sha256:d",
    )
    audit.record_lnurl_auth_event(
        event_type="lnurl_auth_session_created",
        outcome="success",
        principal_hash="hmac-sha256:p",
        session_hash="hmac-sha256:s",
        challenge_hash="sha256:c1",
        auth_domain_hash="sha256:d",
    )


def test_valid_sequence_verifies() -> None:
    audit = make_service()
    populate(audit)
    assert audit.memory_chain is not None

    assert audit.memory_chain.verify_chain()["valid"] is True


def test_reordered_events_fail_verification() -> None:
    audit = make_service()
    populate(audit)
    assert audit.memory_chain is not None
    reordered = [audit.memory_chain.events[1], audit.memory_chain.events[0], audit.memory_chain.events[2]]

    assert audit.memory_chain.verify_chain(reordered)["valid"] is False


def test_broken_previous_hash_fails_verification() -> None:
    audit = make_service()
    populate(audit)
    assert audit.memory_chain is not None
    second = audit.memory_chain.events[1]
    broken_ref = type(second.reference)(
        event_id=second.reference.event_id,
        event_type=second.reference.event_type,
        event_hash=second.reference.event_hash,
        previous_event_hash="sha256:wrong",
        sequence=second.reference.sequence,
        occurred_at=second.reference.occurred_at,
        idempotency_key=second.reference.idempotency_key,
    )
    broken = list(audit.memory_chain.events)
    broken[1] = type(second)(reference=broken_ref, canonical_event=second.canonical_event)

    assert audit.memory_chain.verify_chain(broken)["valid"] is False


def test_replay_attempt_is_distinct_security_event_not_duplicate_success() -> None:
    audit = make_service()
    success = audit.record_lnurl_auth_event(
        event_type="lnurl_auth_callback_succeeded",
        outcome="success",
        principal_hash="hmac-sha256:p",
        challenge_hash="sha256:c1",
        auth_domain_hash="sha256:d",
    )
    replay = audit.record_lnurl_auth_event(
        event_type="lnurl_auth_replay_rejected",
        outcome="replay_rejected",
        principal_hash="hmac-sha256:p",
        challenge_hash="sha256:c1",
        auth_domain_hash="sha256:d",
        reason_code="k1_reused",
    )

    assert replay != success
    assert audit.memory_chain is not None
    assert len(audit.memory_chain.events) == 2


def test_critical_transition_fails_closed_when_audit_persistence_fails() -> None:
    class BrokenChain:
        def record_event(self, **_: object) -> object:
            raise RuntimeError("database down")

    audit = LNURLAuditService(audit_chain=BrokenChain())  # type: ignore[arg-type]

    with pytest.raises(AccessAuditError):
        audit.record_lnurl_auth_event(
            event_type="lnurl_auth_step_up_succeeded",
            outcome="success",
            principal_hash="hmac-sha256:p",
            challenge_hash="sha256:c",
            auth_domain_hash="sha256:d",
        )
