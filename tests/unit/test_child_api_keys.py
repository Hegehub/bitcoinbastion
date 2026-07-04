from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.models.access import ChildApiKey
from app.domain.access.plans import PlanCode
from app.schemas.access import ChildApiKeyCreate
from app.services.access.child_api_keys import ChildApiKeyError, ChildApiKeyService
from app.services.access.key_constraints import ParentAccessContext


def _db() -> Session:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, class_=Session)()


def _parent(plan: PlanCode = PlanCode.PRO, scopes: set[str] | None = None) -> ParentAccessContext:
    return ParentAccessContext(
        pass_lookup_hash="hmac-sha256:parent",
        certificate_fingerprint="sha256:cert",
        plan_code=plan,
        effective_scopes=frozenset(scopes or {"market:intelligence:read", "trace:standard:read", "api:keys:manage"}),
        metric_entitlements=frozenset({"market.intelligence", "trace.standard"}),
        entitlement_expires_at=datetime.now(UTC) + timedelta(days=30),
        session_hash="hmac-sha256:session",
        device_key_fingerprint="sha256:device",
        can_delegate=True,
    )


def _request(scopes: list[str] | None = None, expires_days: int = 1) -> ChildApiKeyCreate:
    return ChildApiKeyCreate(
        name="bot",
        scopes=scopes or ["market:intelligence:read"],
        metric_entitlements={"groups": ["market.intelligence"]},
        limits={"daily_requests": 100},
        expires_at=datetime.now(UTC) + timedelta(days=expires_days),
    )


def test_basic_can_create_only_one_read_only_child_key() -> None:
    db = _db()
    service = ChildApiKeyService(db, server_pepper="pepper")
    parent = _parent(PlanCode.BASIC, {"market:intelligence:read"})
    first = service.create_child_key(parent, _request(), human_intent_signature=None)
    assert first.raw_child_api_key.startswith("bbk_live_")
    with pytest.raises(ValueError, match="child_key_limit_exceeded"):
        service.create_child_key(parent, _request(), human_intent_signature=None)


def test_plus_and_pro_plan_limits() -> None:
    db = _db()
    service = ChildApiKeyService(db, server_pepper="pepper")
    plus = _parent(PlanCode.PLUS)
    for _ in range(3):
        service.create_child_key(plus, _request(), human_intent_signature=None)
    with pytest.raises(ValueError, match="child_key_limit_exceeded"):
        service.create_child_key(plus, _request(), human_intent_signature=None)
    db = _db()
    service = ChildApiKeyService(db, server_pepper="pepper")
    pro = _parent(PlanCode.PRO)
    for _ in range(10):
        service.create_child_key(pro, _request(), human_intent_signature="intent")
    with pytest.raises(ValueError, match="child_key_limit_exceeded"):
        service.create_child_key(pro, _request(), human_intent_signature="intent")


def test_child_scope_expiry_metric_and_human_intent_constraints() -> None:
    db = _db()
    service = ChildApiKeyService(db, server_pepper="pepper")
    parent = _parent(PlanCode.PRO)
    with pytest.raises(ValueError, match="child_scope_exceeds_parent"):
        service.create_child_key(parent, _request(["treasury:read"]), human_intent_signature="intent")
    with pytest.raises(ValueError, match="child_expiry_exceeds_parent"):
        service.create_child_key(parent, _request(expires_days=60), human_intent_signature="intent")
    bad_metric = _request()
    bad_metric.metric_entitlements = {"groups": ["signals.advanced"]}
    with pytest.raises(ValueError, match="child_metric_exceeds_parent"):
        service.create_child_key(parent, bad_metric, human_intent_signature="intent")
    with pytest.raises(ValueError, match="human_intent_required"):
        service.create_child_key(parent, _request(), human_intent_signature=None)


def test_raw_child_key_returned_once_and_not_stored_or_verified_after_revoke() -> None:
    db = _db()
    service = ChildApiKeyService(db, server_pepper="pepper")
    parent = _parent(PlanCode.PRO)
    created = service.create_child_key(parent, _request(), human_intent_signature="intent")
    stored = db.query(ChildApiKey).one()
    assert created.raw_child_api_key not in str(stored.__dict__)
    assert service.verify_child_key(created.raw_child_api_key, "market:intelligence:read").id == stored.id
    service.revoke_child_key(parent, created.key_id, "test")
    with pytest.raises(ChildApiKeyError, match="child_key_revoked"):
        service.verify_child_key(created.raw_child_api_key, "market:intelligence:read")


def test_parent_revocation_and_downgrade_freeze_children() -> None:
    db = _db()
    service = ChildApiKeyService(db, server_pepper="pepper")
    parent = _parent(PlanCode.PRO)
    service.create_child_key(parent, _request(["trace:standard:read"]), human_intent_signature="intent")
    assert service.freeze_invalid_children_after_downgrade(parent.pass_lookup_hash, type("E", (), {"scopes_json": ["market:intelligence:read"]})()) == 1
    row = db.query(ChildApiKey).one()
    row.status = "active"
    assert service.revoke_children_for_parent(parent.pass_lookup_hash, "parent_revoked") == 1
    assert db.query(ChildApiKey).one().status == "revoked"
