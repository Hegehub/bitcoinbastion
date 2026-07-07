from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.models.access import SubscriptionEntitlement
from app.domain.access.decisions import PolicyDecision
from app.domain.access.plans import PlanCode
from app.services.access.crypto.hashing import hmac_sha256_prefixed, sha256_prefixed
from app.services.access.entitlement_service import SubscriptionEntitlementService
from app.services.access.plan_entitlements import get_plan_metric_groups, validate_history_range_allowed, validate_interval_allowed


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
def service() -> SubscriptionEntitlementService:
    engine = create_engine("sqlite:///:memory:")
    SubscriptionEntitlement.__table__.create(bind=engine)
    session = Session(engine)
    private_key, public_key = _key_pair()
    return SubscriptionEntitlementService(session, issuer_private_key=private_key, issuer_public_key=public_key, issuer_key_id="issuer-key-1")


def _issue(service: SubscriptionEntitlementService, plan: PlanCode) -> SubscriptionEntitlement:
    now = datetime.now(UTC)
    return service.issue_entitlement(
        pass_lookup_hash=hmac_sha256_prefixed("pepper", f"pass-{plan.value}"),
        certificate_fingerprint=sha256_prefixed(f"cert-{plan.value}"),
        plan_code=plan,
        valid_from=now,
        valid_until=now + timedelta(days=30),
    )


@pytest.mark.parametrize(
    ("plan", "group", "expected"),
    [
        (PlanCode.LITE, "market.intelligence", PolicyDecision.UPGRADE_REQUIRED),
        (PlanCode.BASIC, "historical.similarity", PolicyDecision.UPGRADE_REQUIRED),
        (PlanCode.PLUS, "historical.similarity", PolicyDecision.ALLOW),
        (PlanCode.PLUS, "signals.advanced", PolicyDecision.UPGRADE_REQUIRED),
        (PlanCode.PRO, "signals.advanced", PolicyDecision.ALLOW),
        (PlanCode.PRO, "payregister.metrics", PolicyDecision.UPGRADE_REQUIRED),
        (PlanCode.BUSINESS, "payregister.metrics", PolicyDecision.ALLOW),
        (PlanCode.ENTERPRISE, "enterprise.custom", PolicyDecision.ALLOW),
    ],
)
def test_metric_group_validation(service: SubscriptionEntitlementService, plan: PlanCode, group: str, expected: PolicyDecision) -> None:
    entitlement = _issue(service, plan)

    assert service.validate_entitlement_for_metric(entitlement, group).decision == expected


def test_enterprise_custom_is_explicit_only() -> None:
    assert "enterprise.custom" not in get_plan_metric_groups(PlanCode.BUSINESS)
    assert "enterprise.custom" in get_plan_metric_groups(PlanCode.ENTERPRISE)


@pytest.mark.parametrize("plan", [PlanCode.LITE, PlanCode.BASIC, PlanCode.PLUS])
def test_lower_plans_reject_1m_interval(service: SubscriptionEntitlementService, plan: PlanCode) -> None:
    entitlement = _issue(service, plan)

    assert service.validate_entitlement_for_interval(entitlement, "1m").decision == PolicyDecision.DENY


def test_pro_allows_1m_interval(service: SubscriptionEntitlementService) -> None:
    entitlement = _issue(service, PlanCode.PRO)

    assert service.validate_entitlement_for_interval(entitlement, "1m").decision == PolicyDecision.ALLOW


def test_malformed_interval_rejected() -> None:
    assert validate_interval_allowed(PlanCode.PRO, "fast") is False


@pytest.mark.parametrize(
    ("plan", "days"),
    [(PlanCode.LITE, 31), (PlanCode.BASIC, 91), (PlanCode.PLUS, 731), (PlanCode.PRO, 1826)],
)
def test_history_range_limits(plan: PlanCode, days: int) -> None:
    assert validate_history_range_allowed(plan, days) is False
