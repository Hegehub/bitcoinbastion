from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.models.access import DelegatedPass
from app.domain.access.plans import PlanCode
from app.schemas.access import DelegatedPassCreate
from app.services.access.delegated_passes import DelegatedPassError, DelegatedPassService
from app.services.access.key_constraints import ParentAccessContext


def _db() -> Session:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, class_=Session)()


def _parent(plan: PlanCode = PlanCode.PRO, scopes: set[str] | None = None, can_delegate: bool = True) -> ParentAccessContext:
    return ParentAccessContext(
        pass_lookup_hash="hmac-sha256:parent",
        certificate_fingerprint="sha256:cert",
        plan_code=plan,
        effective_scopes=frozenset(scopes or {"market:intelligence:read", "trace:standard:read", "payregister:shifts:read"}),
        metric_entitlements=frozenset({"market.intelligence", "trace.standard"}),
        entitlement_expires_at=datetime.now(UTC) + timedelta(days=30),
        can_delegate=can_delegate,
    )


def _request(scopes: list[str] | None = None, expires_days: int = 1, **kwargs) -> DelegatedPassCreate:
    return DelegatedPassCreate(name="delegate", delegated_to_label="analyst", scopes=scopes or ["market:intelligence:read"], metric_entitlements={"groups": ["market.intelligence"]}, constraints=kwargs.pop("constraints", {}), expires_at=datetime.now(UTC) + timedelta(days=expires_days), **kwargs)


def test_delegated_pass_scope_expiry_and_delegation_constraints() -> None:
    db = _db()
    service = DelegatedPassService(db, server_pepper="pepper")
    parent = _parent()
    with pytest.raises(ValueError, match="child_scope_exceeds_parent"):
        service.create_delegated_pass(parent, _request(["treasury:read"]))
    with pytest.raises(ValueError, match="child_expiry_exceeds_parent"):
        service.create_delegated_pass(parent, _request(expires_days=60))
    with pytest.raises(ValueError, match="delegation_not_allowed"):
        service.create_delegated_pass(_parent(can_delegate=False), _request(can_delegate=True))
    with pytest.raises(ValueError, match="delegation_not_allowed"):
        service.create_delegated_pass(_parent(can_delegate=False), _request(can_create_child_keys=True))


def test_raw_delegated_pass_not_stored_expiry_and_revoke() -> None:
    db = _db()
    service = DelegatedPassService(db, server_pepper="pepper")
    parent = _parent()
    created = service.create_delegated_pass(parent, _request())
    stored = db.query(DelegatedPass).one()
    assert created.raw_delegated_pass not in str(stored.__dict__)
    assert service.verify_delegated_pass(created.raw_delegated_pass, "market:intelligence:read").id == stored.id
    service.revoke_delegated_pass(parent, created.delegated_pass_id, "test")
    with pytest.raises(DelegatedPassError, match="delegated_pass_revoked"):
        service.verify_delegated_pass(created.raw_delegated_pass, "market:intelligence:read")


def test_delegated_pass_parent_revocation_downgrade_and_shift_bound_cashier() -> None:
    db = _db()
    service = DelegatedPassService(db, server_pepper="pepper")
    parent = _parent(PlanCode.BUSINESS, {"payregister:shifts:read"})
    created = service.create_delegated_pass(parent, _request(["payregister:shifts:read"], constraints={"shift_id_hash": "sha256:shift"}))
    assert created.raw_delegated_pass.startswith("bbd_live_")
    assert service.freeze_invalid_delegations_after_downgrade(parent.pass_lookup_hash, type("E", (), {"scopes_json": ["market:intelligence:read"]})()) == 1
    row = db.query(DelegatedPass).one()
    row.status = "active"
    assert service.revoke_delegations_for_parent(parent.pass_lookup_hash, "parent_revoked") == 1
    assert db.query(DelegatedPass).one().status == "revoked"
