from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime, timedelta

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.db.models.access import AccessCertificate, AccessRevocation, AccessSession, ChildApiKey, DelegatedPass
from app.services.access.revocation_registry import RevocationRegistry

PASS_HASH = "hmac-sha256:pass"
CERT_FP = "sha256:cert"
DEVICE_FP = "sha256:device"
SESSION_HASH = "hmac-sha256:session"
CHILD_HASH = "hmac-sha256:child"
DELEGATED_HASH = "hmac-sha256:delegated"


def _db() -> Iterator[Session]:
    engine = create_engine("sqlite:///:memory:")
    for table in (
        AccessRevocation.__table__,
        AccessCertificate.__table__,
        AccessSession.__table__,
        ChildApiKey.__table__,
        DelegatedPass.__table__,
    ):
        table.create(bind=engine)
    with Session(engine) as session:
        yield session


def _tree(db: Session) -> None:
    now = datetime.now(UTC)
    db.add(
        AccessCertificate(
            pass_lookup_hash=PASS_HASH,
            pass_commitment="sha256:pass",
            certificate_fingerprint=CERT_FP,
            plan_code="pro_pass",
            status="active",
            device_key_fingerprint=DEVICE_FP,
            issuer_key_id="issuer-test",
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


def test_revoked_access_material_is_denied_and_idempotent() -> None:
    db = next(_db())
    registry = RevocationRegistry()

    first = registry.freeze_session(db, session_hash=SESSION_HASH, reason="session_replay_detected")
    second = registry.freeze_session(db, session_hash=SESSION_HASH, reason="session_replay_detected")
    decision = registry.check_access_material(db, session_hash=SESSION_HASH)

    assert first.revoked is True
    assert second.revocation_epoch == first.revocation_epoch
    assert decision["allowed"] is False
    assert decision["revoked_targets"][0]["target_type"] == "session"
    assert len(db.execute(select(AccessRevocation)).scalars().all()) == 1


def test_revoked_pass_certificate_device_child_and_delegated_material_fail_closed() -> None:
    db = next(_db())
    registry = RevocationRegistry()
    for target_type, target_hash in (
        ("pass", PASS_HASH),
        ("certificate", CERT_FP),
        ("device", DEVICE_FP),
        ("child_api_key", CHILD_HASH),
        ("delegated_pass", DELEGATED_HASH),
    ):
        registry.revoke_target(
            db,
            target_type=target_type,
            target_hash=target_hash,
            reason="manual_security_action",
        )

    decision = registry.check_access_material(
        db,
        pass_lookup_hash=PASS_HASH,
        certificate_fingerprint=CERT_FP,
        device_key_fingerprint=DEVICE_FP,
        child_api_key_hash=CHILD_HASH,
        delegated_pass_hash=DELEGATED_HASH,
    )

    assert decision["allowed"] is False
    assert {target["target_type"] for target in decision["revoked_targets"]} == {
        "pass",
        "certificate",
        "device",
        "child_api_key",
        "delegated_pass",
    }
    assert "bbp_live" not in str(decision)


def test_emergency_lockdown_revokes_pass_tree_and_emits_audit_without_raw_secret() -> None:
    db = next(_db())
    _tree(db)
    audit_events: list[tuple[str, dict[str, object]]] = []
    registry = RevocationRegistry(audit_emitter=lambda event, payload: audit_events.append((event, payload)))

    summary = registry.revoke_pass_tree(
        db,
        pass_lookup_hash=PASS_HASH,
        reason="user_lockdown",
        actor_hash="sha256:actor",
    )

    assert summary["sessions_revoked"] == 1
    assert summary["child_api_keys_revoked"] == 1
    assert summary["delegated_passes_revoked"] == 1
    assert registry.check_access_material(db, pass_lookup_hash=PASS_HASH)["allowed"] is False
    assert audit_events
    assert "bbp_live" not in str(audit_events)
