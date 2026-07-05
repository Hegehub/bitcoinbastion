from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.models.access import AccessSession
from app.schemas.access import AccessLockdownRequest
from app.services.access.lockdown_service import LockdownService


def _db() -> Session:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, class_=Session)()


def _context() -> SimpleNamespace:
    return SimpleNamespace(pass_lookup_hash="hmac-sha256:pass", certificate_fingerprint="sha256:cert", session_hash="hmac-sha256:actor", plan_code="pro_pass", scopes=[], expires_at=datetime.now(UTC) + timedelta(hours=1), device_key_fingerprint="sha256:device")


def test_lockdown_request_rejects_bitcoin_seed_private_key_and_seed_phrase_fields() -> None:
    with pytest.raises(ValueError):
        AccessLockdownRequest.model_validate({"scope": "current_pass", "bitcoin_seed": "abandon abandon abandon"})
    with pytest.raises(ValueError):
        AccessLockdownRequest.model_validate({"scope": "current_pass", "reason": "private_key=abc"})
    with pytest.raises(ValueError):
        AccessLockdownRequest.model_validate({"scope": "current_pass", "reason": "seed_phrase entered"})


def test_lockdown_logs_do_not_contain_raw_session_pass_or_recovery_material(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.INFO)
    db = _db()
    db.add(AccessSession(session_hash="hmac-sha256:s1", certificate_fingerprint="sha256:cert", device_key_fingerprint="sha256:device", scopes_json=[], status="active", created_at=datetime.now(UTC), updated_at=datetime.now(UTC), expires_at=datetime.now(UTC) + timedelta(hours=1)))
    db.flush()
    LockdownService(db).start_lockdown(_context(), AccessLockdownRequest(scope="current_pass", reason="suspected", confirmation_intent_signature="intent"))
    text = caplog.text
    assert "raw_pass" not in text
    assert "session_token" not in text
    assert "recovery_phrase" not in text
    assert "bitcoin_seed" not in text


def test_lockdown_does_not_delete_audit_or_payment_history() -> None:
    db = _db()
    LockdownService(db).start_lockdown(_context(), AccessLockdownRequest(scope="current_pass", reason="suspected", confirmation_intent_signature="intent"))
    from app.db.models.access import AccessAuditEvent

    assert db.query(AccessAuditEvent).count() == 1
