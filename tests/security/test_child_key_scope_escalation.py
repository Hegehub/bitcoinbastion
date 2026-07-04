from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.domain.access.plans import PlanCode
from app.schemas.access import ChildApiKeyCreate
from app.services.access.child_api_keys import ChildApiKeyService
from app.services.access.key_constraints import ParentAccessContext
from app.services.access.key_redaction import assert_no_raw_secret_in_payload, redact_child_key, redact_delegated_pass


def _db() -> Session:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, class_=Session)()


def _parent(plan: PlanCode = PlanCode.PRO) -> ParentAccessContext:
    return ParentAccessContext(
        pass_lookup_hash="hmac-sha256:parent",
        certificate_fingerprint="sha256:cert",
        plan_code=plan,
        effective_scopes=frozenset({"market:intelligence:read", "payregister:metrics:read", "api:keys:manage"}),
        metric_entitlements=frozenset({"market.intelligence", "payregister.metrics"}),
        entitlement_expires_at=datetime.now(UTC) + timedelta(days=30),
        can_delegate=True,
    )


def _request(scope: str) -> ChildApiKeyCreate:
    return ChildApiKeyCreate(name="bad", scopes=[scope], metric_entitlements={}, limits={}, expires_at=datetime.now(UTC) + timedelta(days=1))


@pytest.mark.parametrize("scope", ["api:all", "metrics:all", "admin:all"])
def test_wildcard_scopes_rejected(scope: str) -> None:
    with pytest.raises(ValueError, match="unsafe_scope"):
        ChildApiKeyService(_db(), server_pepper="pepper").create_child_key(_parent(), _request(scope), human_intent_signature="intent")


def test_child_key_cannot_add_treasury_scope_if_parent_lacks_it() -> None:
    with pytest.raises(ValueError, match="child_scope_exceeds_parent"):
        ChildApiKeyService(_db(), server_pepper="pepper").create_child_key(_parent(), _request("treasury:read"), human_intent_signature="intent")


def test_payregister_admin_and_enterprise_scopes_require_entitled_parent_and_plan() -> None:
    with pytest.raises(ValueError):
        ChildApiKeyService(_db(), server_pepper="pepper").create_child_key(_parent(PlanCode.PRO), _request("payregister:admin"), human_intent_signature="intent")
    with pytest.raises(ValueError, match="child_scope_requires_enterprise|child_scope_exceeds_parent"):
        ChildApiKeyService(_db(), server_pepper="pepper").create_child_key(_parent(PlanCode.BUSINESS), _request("enterprise:policy:custom"), human_intent_signature="intent")


def test_raw_child_and_delegated_secrets_are_redacted_and_rejected_from_payloads() -> None:
    assert redact_child_key("bbk_live_id_secret") == "bbk_live_…redacted"
    assert redact_delegated_pass("bbd_live_id_secret") == "bbd_live_…redacted"
    with pytest.raises(ValueError):
        assert_no_raw_secret_in_payload({"raw_child_api_key": "bbk_live_id_secret"})
