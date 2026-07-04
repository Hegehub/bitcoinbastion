from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.models.access import AccessAuditEvent
from app.services.access.audit_chain import AccessAuditChain, build_canonical_event, compute_event_hash

FIXED_TIME = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)


@pytest.fixture()
def db_session() -> Iterator[Session]:
    engine = create_engine("sqlite:///:memory:")
    AccessAuditEvent.__table__.create(bind=engine)
    with Session(engine) as session:
        yield session


def test_canonical_event_is_stable() -> None:
    first = build_canonical_event(
        event_type="session_created",
        actor_hash="sha256:actor",
        metadata={"b": 2, "a": 1},
        occurred_at=FIXED_TIME,
    )
    second = build_canonical_event(
        event_type="session_created",
        actor_hash="sha256:actor",
        metadata={"a": 1, "b": 2},
        occurred_at=FIXED_TIME,
    )

    assert compute_event_hash(None, first) == compute_event_hash(None, second)


def test_event_hash_changes_when_payload_changes() -> None:
    first = build_canonical_event(event_type="policy_allowed", metadata={"scope": "a"}, occurred_at=FIXED_TIME)
    second = build_canonical_event(event_type="policy_allowed", metadata={"scope": "b"}, occurred_at=FIXED_TIME)

    assert compute_event_hash(None, first) != compute_event_hash(None, second)


def test_chain_verifies_when_untouched(db_session: Session) -> None:
    chain = AccessAuditChain(db_session)
    chain.record_event(event_type="payment_settled", object_hash="sha256:payment")
    chain.record_certificate_issued(certificate_fingerprint="sha256:cert")
    chain.record_session_created(session_hash="hmac-sha256:session")

    result = chain.verify_chain()

    assert result == {
        "valid": True,
        "checked_events": 3,
        "first_broken_event_id": None,
        "expected_hash": None,
        "actual_hash": None,
    }


def test_chain_verification_fails_after_tamper(db_session: Session) -> None:
    chain = AccessAuditChain(db_session)
    chain.record_event(event_type="payment_settled", object_hash="sha256:payment")
    event = chain.record_certificate_issued(certificate_fingerprint="sha256:cert")
    chain.record_session_created(session_hash="hmac-sha256:session")
    event.canonical_event_json = {**event.canonical_event_json, "metadata": {"tampered": True}}
    db_session.flush()

    result = chain.verify_chain()

    assert result["valid"] is False
    assert result["first_broken_event_id"] == event.id
    assert result["expected_hash"] != result["actual_hash"]


@pytest.mark.parametrize("key", ["raw_pass", "session_token", "recovery_phrase", "bitcoin_seed", "password"])
def test_forbidden_secret_metadata_rejected(db_session: Session, key: str) -> None:
    chain = AccessAuditChain(db_session)

    with pytest.raises(ValueError):
        chain.record_event(event_type="session_created", metadata={key: "secret-value"})


def test_legacy_auth_disabled_event(db_session: Session) -> None:
    chain = AccessAuditChain(db_session)

    event = chain.record_legacy_auth_disabled(metadata={"route": "/api/v1/auth/login"})

    assert event.event_type == "legacy_auth_disabled"
    assert event.event_hash


def test_previous_event_hash_links_chain(db_session: Session) -> None:
    chain = AccessAuditChain(db_session)
    first = chain.record_event(event_type="payment_settled", object_hash="sha256:payment")
    second = chain.record_certificate_issued(certificate_fingerprint="sha256:cert")

    assert second.previous_event_hash == first.event_hash


def test_no_global_user_id_required(db_session: Session) -> None:
    chain = AccessAuditChain(db_session)

    event = chain.record_event(event_type="policy_denied", actor_hash="sha256:actor", object_hash="sha256:object")

    assert event.actor_hash == "sha256:actor"
    assert event.object_hash == "sha256:object"
    assert "user_id" not in event.canonical_event_json
