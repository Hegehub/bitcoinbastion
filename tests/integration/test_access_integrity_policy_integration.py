from datetime import UTC, datetime, timedelta

from app.domain.access.plans import PlanCode
from app.services.access.policy_context import (
    AccessPolicyContext,
    PolicyActorType,
    PolicyAuthMethod,
)
from app.services.access.policy_engine import AccessPolicyEngine


def context(**changes: object) -> AccessPolicyContext:
    values = dict(
        actor_type=PolicyActorType.LIGHTNING_WALLET_PRINCIPAL,
        actor_hash="hmac:actor",
        principal_hash="hmac:principal",
        auth_methods=frozenset({PolicyAuthMethod.LNURL_AUTH, PolicyAuthMethod.SESSION_POP}),
        plan_code=PlanCode.PRO,
        effective_scopes={"market:intelligence:read"},
        requested_action="read_metric",
        session_id_hash="hmac:session",
        device_id="sha256:device",
        access_integrity_score=95,
        access_integrity_band="excellent",
        integrity_score_version="2.0",
        integrity_evidence_fresh_until=datetime.now(UTC) + timedelta(minutes=5),
    )
    values.update(changes)
    return AccessPolicyContext(**values)


def test_excellent_score_cannot_add_scope_or_metric_entitlement() -> None:
    scope = AccessPolicyEngine().evaluate(context(requested_scope="treasury:write"))
    metric = AccessPolicyEngine().evaluate(
        context(
            requested_scope="market:intelligence:read",
            requested_metric_group="pro",
            metric_entitlements={},
        )
    )
    assert not scope.allowed and not metric.allowed


def test_guarded_restricted_and_critical_only_restrict() -> None:
    guarded = AccessPolicyEngine().evaluate(
        context(
            access_integrity_score=60,
            access_integrity_band="guarded",
            request_risk_level="high",
            requested_scope="market:intelligence:read",
        )
    )
    restricted = AccessPolicyEngine().evaluate(
        context(access_integrity_score=40, access_integrity_band="restricted")
    )
    critical = AccessPolicyEngine().evaluate(
        context(access_integrity_score=10, access_integrity_band="critical")
    )
    assert guarded.decision == "step_up_required"
    assert not restricted.allowed and critical.decision == "lockdown_active"


def test_revocation_and_expired_entitlement_override_excellent_score() -> None:
    revoked = AccessPolicyEngine().evaluate(context(revocation_resolution={"revoked": True}))
    expired = AccessPolicyEngine().evaluate(context(entitlement_status="expired"))
    assert revoked.decision == "revoked" and expired.decision == "expired"
