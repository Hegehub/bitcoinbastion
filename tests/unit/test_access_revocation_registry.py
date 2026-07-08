from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.db.models.access import AccessCertificate, AccessRevocation, AccessSession, ChildApiKey, DelegatedPass
from app.services.access.revocation_registry import (
    InvalidRevocationReasonError,
    InvalidRevocationTargetTypeError,
    REVOCATION_REASONS,
    REVOCATION_TARGET_TYPES,
    RevocationRegistry,
    RevocationRegistryError,
)

SESSION_HASH = "hmac-sha256:session"
PASS_HASH = "hmac-sha256:pass"
CERT_FP = "sha256:cert"
DEVICE_FP = "sha256:device"
CHILD_HASH = "hmac-sha256:child"
DELEGATED_HASH = "hmac-sha256:delegated"


@pytest.fixture()
def db_session() -> Iterator[Session]:
    engine = create_engine("sqlite:///:memory:")
    AccessRevocation.__table__.create(bind=engine)
    AccessCertificate.__table__.create(bind=engine)
    AccessSession.__table__.create(bind=engine)
    ChildApiKey.__table__.create(bind=engine)
    DelegatedPass.__table__.create(bind=engine)
    with Session(engine) as session:
        yield session


@pytest.fixture()
def audit_events() -> list[tuple[str, dict[str, object]]]:
    return []


@pytest.fixture()
def registry(audit_events: list[tuple[str, dict[str, object]]]) -> RevocationRegistry:
    return RevocationRegistry(audit_emitter=lambda event_type, payload: audit_events.append((event_type, payload)))


def _access_tree(db: Session) -> None:
    now = datetime.now(UTC)
    db.add(
        AccessCertificate(
            pass_lookup_hash=PASS_HASH,
            pass_commitment="sha256:pass",
            certificate_fingerprint=CERT_FP,
            plan_code="pro_pass",
            status="active",
            device_key_fingerprint=DEVICE_FP,
            issuer_key_id="issuer-key-1",
            crypto_epoch=1,
            scopes_json=["market:intelligence:read"],
            issuer_signature_json={},
            issued_at=now,
            expires_at=now + timedelta(days=30),
        )
    )
    db.add(
        AccessSession(
            session_hash=SESSION_HASH,
            certificate_fingerprint=CERT_FP,
            device_key_fingerprint=DEVICE_FP,
            scopes_json=["market:intelligence:read"],
            status="active",
            risk_level="low",
            expires_at=now + timedelta(minutes=15),
        )
    )
    db.add(
        ChildApiKey(
            parent_pass_lookup_hash=PASS_HASH,
            key_id_hash=CHILD_HASH,
            key_secret_hash="hmac-sha256:child-secret",
            scopes_json=["market:intelligence:read"],
            status="active",
            expires_at=now + timedelta(days=1),
        )
    )
    db.add(
        DelegatedPass(
            parent_pass_lookup_hash=PASS_HASH,
            delegated_pass_hash=DELEGATED_HASH,
            scopes_json=["market:intelligence:read"],
            constraints_json={"max_uses": 1},
            status="active",
            valid_from=now,
            valid_until=now + timedelta(days=1),
        )
    )
    db.flush()


def test_revoke_target_creates_revocation(db_session: Session, registry: RevocationRegistry) -> None:
    status = registry.revoke_target(
        db_session,
        target_type="session",
        target_hash=SESSION_HASH,
        reason="session_replay_detected",
    )

    assert status.revoked is True
    assert registry.is_revoked(db_session, target_type="session", target_hash=SESSION_HASH).revoked is True


def test_revoke_target_is_idempotent(db_session: Session, registry: RevocationRegistry) -> None:
    first = registry.revoke_target(db_session, target_type="session", target_hash=SESSION_HASH, reason="admin_policy")
    second = registry.revoke_target(db_session, target_type="session", target_hash=SESSION_HASH, reason="admin_policy")
    rows = db_session.execute(select(AccessRevocation)).scalars().all()

    assert len(rows) == 1
    assert first.revocation_epoch == second.revocation_epoch
    assert second.revoked is True


def test_unknown_target_is_not_revoked(db_session: Session, registry: RevocationRegistry) -> None:
    status = registry.is_revoked(db_session, target_type="session", target_hash=SESSION_HASH)

    assert status.revoked is False
    assert status.decision_hint == "not_revoked"


def test_invalid_target_type_rejected(db_session: Session, registry: RevocationRegistry) -> None:
    with pytest.raises(InvalidRevocationTargetTypeError):
        registry.revoke_target(db_session, target_type="bearer_token", target_hash=SESSION_HASH, reason="admin_policy")


def test_invalid_reason_rejected(db_session: Session, registry: RevocationRegistry) -> None:
    with pytest.raises(InvalidRevocationReasonError):
        registry.revoke_target(db_session, target_type="session", target_hash=SESSION_HASH, reason="because")


def test_freeze_session_revokes_session(db_session: Session, registry: RevocationRegistry) -> None:
    registry.freeze_session(db_session, session_hash=SESSION_HASH, reason="session_replay_detected")
    result = registry.check_access_material(db_session, session_hash=SESSION_HASH)

    assert result["allowed"] is False
    assert result["revoked_targets"][0]["target_type"] == "session"


def test_revoke_device_blocks_device_material(db_session: Session, registry: RevocationRegistry) -> None:
    registry.revoke_device(db_session, device_key_fingerprint=DEVICE_FP, reason="device_lost")
    result = registry.check_access_material(db_session, device_key_fingerprint=DEVICE_FP)

    assert result["decision"] == "revoked"
    assert result["revoked_targets"][0]["target_hash"] == DEVICE_FP


def test_revoke_pass_tree_is_safe(db_session: Session, registry: RevocationRegistry) -> None:
    _access_tree(db_session)

    summary = registry.revoke_pass_tree(db_session, pass_lookup_hash=PASS_HASH, reason="user_lockdown")

    assert summary["pass_revoked"] is True
    assert summary["sessions_revoked"] == 1
    assert summary["child_api_keys_revoked"] == 1
    assert summary["delegated_passes_revoked"] == 1
    assert summary["offline_packs_invalidated"] == 0
    assert summary["warnings"] == []


def test_check_access_material_multiple_targets(db_session: Session, registry: RevocationRegistry) -> None:
    registry.revoke_target(db_session, target_type="device", target_hash=DEVICE_FP, reason="device_lost")

    result = registry.check_access_material(
        db_session,
        pass_lookup_hash=PASS_HASH,
        certificate_fingerprint=CERT_FP,
        device_key_fingerprint=DEVICE_FP,
        session_hash=SESSION_HASH,
    )

    assert result["allowed"] is False
    assert result["revoked_targets"] == [
        {"target_type": "device", "target_hash": DEVICE_FP, "reason": "device_lost", "revocation_epoch": 1}
    ]


def test_revocation_does_not_store_raw_secret(db_session: Session, registry: RevocationRegistry) -> None:
    raw_pass = "bbp_live_secret_not_real"

    with pytest.raises(RevocationRegistryError):
        registry.revoke_target(db_session, target_type="pass", target_hash=raw_pass, reason="admin_policy")
    registry.revoke_target(
        db_session,
        target_type="pass",
        target_hash=PASS_HASH,
        reason="admin_policy",
        metadata={"raw_access_pass": raw_pass},
    )
    row = db_session.execute(select(AccessRevocation)).scalar_one()

    assert row.target_hash == PASS_HASH
    assert raw_pass not in str(row.metadata_json)
    assert row.metadata_json == {"raw_access_pass": "[REDACTED]"}


def test_audit_event_emitted_when_available(db_session: Session, registry: RevocationRegistry, audit_events: list[tuple[str, dict[str, object]]]) -> None:
    registry.revoke_target(
        db_session,
        target_type="session",
        target_hash=SESSION_HASH,
        reason="manual_security_action",
        actor_hash="sha256:actor",
    )

    assert audit_events
    event_type, payload = audit_events[0]
    assert event_type == "access_target_revoked"
    assert payload["target_hash"] == SESSION_HASH
    assert "raw" not in str(payload).lower()


def test_lockdown_reason_supported(db_session: Session, registry: RevocationRegistry) -> None:
    status = registry.revoke_target(db_session, target_type="pass", target_hash=PASS_HASH, reason="user_lockdown")

    assert status.reason == "user_lockdown"
    assert "business_role" in REVOCATION_TARGET_TYPES
    assert "issuer_key_compromised" in REVOCATION_REASONS
