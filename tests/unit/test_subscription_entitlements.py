from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.models.access import SubscriptionEntitlement
from app.domain.access.decisions import PolicyDecision
from app.domain.access.plans import PlanCode
from app.services.access.crypto.hashing import hmac_sha256_prefixed, sha256_prefixed
from app.services.access.entitlement_service import (
    EntitlementIntegrityError,
    SubscriptionEntitlementService,
    canonical_entitlement_payload,
)


def _key_pair() -> tuple[str, str]:
    private_key = Ed25519PrivateKey.generate()
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")
    public_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")
    return private_pem, public_pem


@pytest.fixture()
def db_session() -> Session:
    engine = create_engine("sqlite:///:memory:")
    SubscriptionEntitlement.__table__.create(bind=engine)
    with Session(engine) as session:
        yield session


@pytest.fixture()
def service(db_session: Session) -> SubscriptionEntitlementService:
    private_key, public_key = _key_pair()
    return SubscriptionEntitlementService(
        db_session,
        issuer_private_key=private_key,
        issuer_public_key=public_key,
        issuer_key_id="issuer-key-1",
    )


def _ids(label: str = "one") -> tuple[str, str]:
    return hmac_sha256_prefixed("pepper", f"pass-{label}"), sha256_prefixed(f"certificate-{label}")


def _window(days: int = 30) -> tuple[datetime, datetime]:
    start = datetime.now(UTC)
    return start, start + timedelta(days=days)


def _issue(service: SubscriptionEntitlementService, plan: PlanCode = PlanCode.PLUS, label: str = "one") -> SubscriptionEntitlement:
    pass_hash, cert_fp = _ids(label)
    valid_from, valid_until = _window()
    return service.issue_entitlement(
        pass_lookup_hash=pass_hash,
        certificate_fingerprint=cert_fp,
        plan_code=plan,
        valid_from=valid_from,
        valid_until=valid_until,
        grace_until=valid_until + timedelta(days=3),
    )


@pytest.mark.parametrize("plan", list(PlanCode))
def test_issue_all_plans(service: SubscriptionEntitlementService, plan: PlanCode) -> None:
    entitlement = _issue(service, plan, label=plan.value)

    assert entitlement.plan_code == plan.value
    assert entitlement.status == "active"
    assert entitlement.scopes_json
    assert entitlement.metric_entitlements_json["groups"]
    assert service.verify_entitlement_signature(entitlement) is True


def test_unknown_plan_rejected(service: SubscriptionEntitlementService) -> None:
    pass_hash, cert_fp = _ids()
    valid_from, valid_until = _window()

    with pytest.raises(Exception):
        service.issue_entitlement(
            pass_lookup_hash=pass_hash,
            certificate_fingerprint=cert_fp,
            plan_code="interprise",
            valid_from=valid_from,
            valid_until=valid_until,
        )


def test_entitlement_without_valid_until_rejected(service: SubscriptionEntitlementService) -> None:
    pass_hash, cert_fp = _ids()
    valid_from = datetime.now(UTC)

    with pytest.raises(EntitlementIntegrityError):
        service.issue_entitlement(
            pass_lookup_hash=pass_hash,
            certificate_fingerprint=cert_fp,
            plan_code=PlanCode.LITE,
            valid_from=valid_from,
            valid_until=valid_from,
        )


def test_active_current_entitlement_returned(service: SubscriptionEntitlementService) -> None:
    entitlement = _issue(service, PlanCode.BASIC)

    current = service.get_current_entitlement(pass_lookup_hash=entitlement.pass_lookup_hash)

    assert current is not None
    assert current.id == entitlement.id


def test_expired_entitlement_denied(service: SubscriptionEntitlementService) -> None:
    entitlement = _issue(service, PlanCode.PRO)
    service.expire_entitlement(entitlement)

    assert service.get_current_entitlement(pass_lookup_hash=entitlement.pass_lookup_hash) is None
    assert service.validate_entitlement_for_metric(entitlement, "signals.advanced").decision == PolicyDecision.EXPIRED


def test_revoked_entitlement_denied(service: SubscriptionEntitlementService) -> None:
    entitlement = _issue(service, PlanCode.PRO)
    service.revoke_entitlement(entitlement)

    assert service.validate_entitlement_for_scope(entitlement, "signals:advanced:read").decision == PolicyDecision.REVOKED


def test_frozen_entitlement_returns_restricted_decision(service: SubscriptionEntitlementService) -> None:
    entitlement = _issue(service, PlanCode.PRO)
    service.freeze_entitlement(entitlement)

    assert service.validate_entitlement_for_scope(entitlement, "signals:advanced:read").decision == PolicyDecision.FROZEN


def test_plus_to_pro_expands_allowed_metrics_and_audits(db_session: Session) -> None:
    events: list[tuple[str, dict[str, Any]]] = []
    private_key, public_key = _key_pair()
    service = SubscriptionEntitlementService(
        db_session,
        issuer_private_key=private_key,
        issuer_public_key=public_key,
        issuer_key_id="issuer-key-1",
        audit_emitter=lambda event, payload: events.append((event, payload)),
    )
    entitlement = _issue(service, PlanCode.PLUS)
    start, end = _window()

    upgraded = service.upgrade_entitlement(entitlement, new_plan_code=PlanCode.PRO, valid_from=start, valid_until=end)

    assert "signals.advanced" in upgraded.metric_entitlements_json["groups"]
    assert upgraded.metadata_json["child_keys_not_modified"] is True
    assert any(event == "entitlement_upgraded" for event, _ in events)


def test_pro_to_plus_removes_advanced_signals(service: SubscriptionEntitlementService) -> None:
    entitlement = _issue(service, PlanCode.PRO)
    start, end = _window()

    downgraded = service.downgrade_entitlement(entitlement, new_plan_code=PlanCode.PLUS, valid_from=start, valid_until=end)

    assert "signals.advanced" not in downgraded.metric_entitlements_json["groups"]
    assert downgraded.metadata_json["child_key_review_required"] is True


def test_business_to_pro_removes_payregister_metrics(service: SubscriptionEntitlementService) -> None:
    entitlement = _issue(service, PlanCode.BUSINESS)
    start, end = _window()

    downgraded = service.downgrade_entitlement(entitlement, new_plan_code=PlanCode.PRO, valid_from=start, valid_until=end)

    assert "payregister.metrics" not in downgraded.metric_entitlements_json["groups"]


def test_public_response_hides_pass_lookup_hash(service: SubscriptionEntitlementService) -> None:
    entitlement = _issue(service, PlanCode.PLUS)

    response = service.to_public_response(entitlement)

    assert "pass_lookup_hash" not in response
    assert "raw_access_pass" not in response
    assert response["plan_code"] == PlanCode.PLUS.value


def test_canonical_entitlement_payload_is_stable() -> None:
    assert canonical_entitlement_payload({"b": 2, "a": 1}) == canonical_entitlement_payload({"a": 1, "b": 2})
