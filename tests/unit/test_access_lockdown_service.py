from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.models.access import AccessAuditEvent, AccessDevice, AccessSession, ChildApiKey, DelegatedPass
from app.schemas.access import AccessLockdownRequest, AccessLockdownScope
from app.services.access.lockdown_service import LockdownError, LockdownService
from app.services.access.policy_context import AccessPolicyDecision


def _db() -> Session:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, class_=Session)()


def _context() -> SimpleNamespace:
    return SimpleNamespace(
        pass_lookup_hash="hmac-sha256:pass",
        certificate_fingerprint="sha256:cert",
        session_hash="hmac-sha256:actor-session",
        plan_code="pro_pass",
        scopes=["api:keys:manage"],
        expires_at=datetime.now(UTC) + timedelta(hours=1),
        device_key_fingerprint="sha256:device",
        workspace_id_hash=None,
    )


def _seed(db: Session) -> None:
    db.add(AccessSession(session_hash="hmac-sha256:s1", certificate_fingerprint="sha256:cert", device_key_fingerprint="sha256:device", scopes_json=["api:keys:manage"], status="active", created_at=datetime.now(UTC), updated_at=datetime.now(UTC), expires_at=datetime.now(UTC) + timedelta(hours=1)))
    db.add(ChildApiKey(parent_pass_lookup_hash="hmac-sha256:pass", key_id_hash="hmac-sha256:key", key_secret_hash="hmac-sha256:key-secret", name="bot", scopes_json=["market:intelligence:read"], limits_json={}, cannot_access_json=[], status="active", expires_at=datetime.now(UTC) + timedelta(days=1)))
    db.add(DelegatedPass(parent_pass_lookup_hash="hmac-sha256:pass", delegated_pass_hash="hmac-sha256:delegated", delegated_to_hash=None, scopes_json=["market:intelligence:read"], constraints_json={}, status="active", valid_from=datetime.now(UTC), valid_until=datetime.now(UTC) + timedelta(days=1)))
    db.add(AccessDevice(certificate_fingerprint="sha256:cert", device_key_fingerprint="sha256:device", device_public_key="pub", device_class="desktop", status="active"))
    db.flush()


def _request() -> AccessLockdownRequest:
    return AccessLockdownRequest(scope=AccessLockdownScope.CURRENT_PASS, reason="suspected_device_compromise", confirmation_intent_signature="intent", recovery_mode=True)


def test_current_pass_lockdown_freezes_sessions_and_access_fails() -> None:
    db = _db()
    _seed(db)
    result = LockdownService(db).start_lockdown(_context(), _request())
    assert result.status == "locked_down"
    assert result.affected_sessions == 1
    assert db.query(AccessSession).one().status == "frozen"


def test_child_api_keys_and_delegated_passes_revoked() -> None:
    db = _db()
    _seed(db)
    result = LockdownService(db).start_lockdown(_context(), _request())
    assert result.affected_child_api_keys == 1
    assert result.affected_delegated_passes == 1
    assert db.query(ChildApiKey).one().status == "revoked"
    assert db.query(DelegatedPass).one().status == "revoked"


def test_lockdown_is_idempotent_and_audit_chain_valid() -> None:
    db = _db()
    _seed(db)
    service = LockdownService(db)
    first = service.start_lockdown(_context(), _request())
    second = service.start_lockdown(_context(), _request())
    assert first.affected_sessions == 1
    assert second.affected_sessions == 0
    assert db.query(AccessAuditEvent).count() >= 2
    assert service.audit_chain.verify_chain()["valid"] is True


def test_audit_event_created_without_raw_secret_material() -> None:
    db = _db()
    _seed(db)
    result = LockdownService(db).start_lockdown(_context(), _request())
    event = db.query(AccessAuditEvent).filter(AccessAuditEvent.event_hash == result.audit_event_hash).one()
    assert event.event_hash
    assert "raw_pass" not in str(event.canonical_event_json)
    assert "session_token" not in str(event.canonical_event_json)


class DenyPolicy:
    def evaluate(self, context):
        return AccessPolicyDecision(decision="deny", allowed=False, reason_code="policy_denied", human_reason="Denied")


def test_policy_denial_prevents_lockdown() -> None:
    db = _db()
    _seed(db)
    with pytest.raises(LockdownError, match="policy_denied"):
        LockdownService(db, policy_engine=DenyPolicy()).start_lockdown(_context(), _request())
    assert db.query(AccessSession).one().status == "active"


def test_missing_human_intent_signature_fails() -> None:
    db = _db()
    _seed(db)
    with pytest.raises(LockdownError, match="step_up_required"):
        LockdownService(db).start_lockdown(_context(), AccessLockdownRequest(scope="current_pass"))
