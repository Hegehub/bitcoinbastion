from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from app.domain.access.plans import PlanCode
from app.domain.access.scopes import (
    MARKET_INTELLIGENCE_READ,
    METRICS_BASIC_READ,
    PAYREGISTER_ADMIN,
    PAYREGISTER_DEVICES_READ,
    TRACE_ADVANCED_READ,
    TREASURY_POLICY_READ,
)
from app.services.access.plan_entitlements import build_entitlement_overlay
from app.services.access.policy_context import AccessPolicyContext
from app.services.access.policy_engine import AccessPolicyEngine
from app.services.access import policy_reasons as reasons


def _ctx(plan: PlanCode | str = PlanCode.PLUS, **overrides: object) -> AccessPolicyContext:
    overlay = build_entitlement_overlay(plan)  # type: ignore[arg-type]
    data = {
        "certificate_fingerprint": "sha256:cert",
        "pass_lookup_hash": "hmac-sha256:pass",
        "plan_code": plan,
        "effective_scopes": set(overlay["allowed_scopes"]),
        "session_id_hash": "hmac-sha256:session",
        "session_status": "active",
        "session_expires_at": datetime.now(UTC) + timedelta(minutes=15),
        "device_id": "device-1",
        "device_status": "active",
        "device_risk_score": 10,
        "entitlement_status": "active",
        "entitlement_valid_until": datetime.now(UTC) + timedelta(days=30),
        "entitlement_limits": overlay["limits"],
        "metric_entitlements": {"groups": overlay["metric_groups"]},
        "quota_state": {"remaining": 1000},
        "revocation_state": {"allowed": True, "revoked_targets": []},
        "request_risk_level": "low",
    }
    data.update(overrides)
    return AccessPolicyContext(**data)  # type: ignore[arg-type]


def test_lite_can_access_basic_metrics() -> None:
    decision = AccessPolicyEngine().evaluate(_ctx(PlanCode.LITE, requested_scope=METRICS_BASIC_READ, requested_metric_group="market.basic", requested_metric_name="btc.price"))

    assert decision.allowed is True
    assert decision.reason_code == reasons.ACCESS_ALLOWED


def test_lite_cannot_access_market_intelligence() -> None:
    decision = AccessPolicyEngine().evaluate(_ctx(PlanCode.LITE, requested_metric_group="market.intelligence"))

    assert decision.decision == "upgrade_required"
    assert decision.required_plan == PlanCode.PLUS


def test_plus_can_access_market_intelligence() -> None:
    decision = AccessPolicyEngine().evaluate(_ctx(PlanCode.PLUS, requested_scope=MARKET_INTELLIGENCE_READ, requested_metric_group="market.intelligence"))

    assert decision.allowed is True


def test_plus_cannot_access_signals_advanced() -> None:
    decision = AccessPolicyEngine().evaluate(_ctx(PlanCode.PLUS, requested_metric_group="signals.advanced"))

    assert decision.decision == "upgrade_required"
    assert decision.reason_code == reasons.METRIC_REQUIRES_HIGHER_PLAN


def test_plus_signals_advanced_requires_pro() -> None:
    decision = AccessPolicyEngine().evaluate(_ctx(PlanCode.PLUS, requested_metric_group="signals.advanced"))

    assert decision.required_plan == PlanCode.PRO
    assert decision.upgrade_available is True
    assert decision.requested_metric_group == "signals.advanced"


def test_pro_can_access_trace_advanced() -> None:
    decision = AccessPolicyEngine().evaluate(_ctx(PlanCode.PRO, requested_scope=TRACE_ADVANCED_READ, requested_metric_group="trace.advanced"))

    assert decision.allowed is True


def test_expired_entitlement_returns_expired() -> None:
    decision = AccessPolicyEngine().evaluate(_ctx(entitlement_valid_until=datetime.now(UTC) - timedelta(seconds=1)))

    assert decision.decision == "expired"
    assert decision.reason_code == reasons.ENTITLEMENT_EXPIRED


def test_revoked_session_returns_revoked() -> None:
    decision = AccessPolicyEngine().evaluate(_ctx(session_status="revoked"))

    assert decision.decision == "revoked"
    assert decision.reason_code == reasons.SESSION_REVOKED


def test_revoked_certificate_returns_revoked() -> None:
    decision = AccessPolicyEngine().evaluate(_ctx(revocation_state={"allowed": False, "revoked_targets": [{"target_type": "certificate"}]}))

    assert decision.decision == "revoked"
    assert decision.reason_code == reasons.CERTIFICATE_REVOKED


def test_missing_scope_returns_deny() -> None:
    decision = AccessPolicyEngine().evaluate(_ctx(PlanCode.LITE, requested_scope=MARKET_INTELLIGENCE_READ))

    assert decision.allowed is False
    assert decision.reason_code == reasons.SCOPE_NOT_ALLOWED


def test_unknown_scope_returns_deny() -> None:
    decision = AccessPolicyEngine().evaluate(_ctx(requested_scope="unknown:scope"))

    assert decision.reason_code == reasons.SCOPE_NOT_ALLOWED


def test_unknown_metric_group_returns_deny() -> None:
    decision = AccessPolicyEngine().evaluate(_ctx(requested_metric_group="unknown.metrics"))

    assert decision.decision == "metric_not_allowed"


def test_quota_exhausted_returns_quota_exceeded() -> None:
    decision = AccessPolicyEngine().evaluate(_ctx(quota_state={"exhausted": True, "remaining": 0, "retry_after_seconds": 60}))

    assert decision.decision == "quota_exceeded"
    assert decision.retry_after_seconds == 60


def test_high_risk_action_returns_step_up_required() -> None:
    decision = AccessPolicyEngine().evaluate(_ctx(request_risk_level="high"))

    assert decision.decision == "step_up_required"
    assert decision.step_up_required is True


def test_critical_action_without_human_intent_returns_step_up_required() -> None:
    decision = AccessPolicyEngine().evaluate(_ctx(is_critical_action=True, step_up_present=True, human_intent_verified=False))

    assert decision.decision == "step_up_required"
    assert decision.reason_code == reasons.CRITICAL_ACTION_REQUIRES_HUMAN_INTENT


def test_critical_action_with_human_intent_can_allow() -> None:
    decision = AccessPolicyEngine().evaluate(_ctx(is_critical_action=True, step_up_present=True, human_intent_verified=True))

    assert decision.allowed is True
    assert decision.audit_required is True


def test_business_cashier_cannot_access_payregister_admin() -> None:
    decision = AccessPolicyEngine().evaluate(
        _ctx(PlanCode.BUSINESS, requested_scope=PAYREGISTER_ADMIN, requested_object_type="payregister_device", requested_object_id_hash="sha256:device", business_role="cashier")
    )

    assert decision.reason_code in {reasons.SCOPE_NOT_ALLOWED, reasons.BUSINESS_ROLE_DENIED}


def test_business_admin_can_access_payregister_devices() -> None:
    decision = AccessPolicyEngine().evaluate(
        _ctx(PlanCode.BUSINESS, requested_scope=PAYREGISTER_DEVICES_READ, requested_object_type="payregister_device", requested_object_id_hash="sha256:device", business_role="admin")
    )

    assert decision.allowed is True


def test_offline_pro_non_critical_cached_action_can_allow() -> None:
    decision = AccessPolicyEngine().evaluate(_ctx(PlanCode.PRO, offline_mode=True, requested_scope=MARKET_INTELLIGENCE_READ, requested_metric_group="market.intelligence"))

    assert decision.allowed is True


def test_offline_treasury_admin_request_denies() -> None:
    decision = AccessPolicyEngine().evaluate(_ctx(PlanCode.PRO, offline_mode=True, requested_scope=TREASURY_POLICY_READ, is_critical_action=True))

    assert decision.decision == "online_check_required"


def test_object_access_unknown_denies() -> None:
    decision = AccessPolicyEngine().evaluate(_ctx(requested_object_type="trace_report"))

    assert decision.reason_code == reasons.OBJECT_ACCESS_DENIED


def test_no_global_user_id_is_required() -> None:
    decision = AccessPolicyEngine().evaluate(_ctx(requested_scope=MARKET_INTELLIGENCE_READ))

    assert decision.allowed is True


@pytest.mark.parametrize("scope", ["api:all", "metrics:all"])
def test_wildcard_scope_rejected(scope: str) -> None:
    decision = AccessPolicyEngine().evaluate(_ctx(effective_scopes={scope}, requested_scope=scope))

    assert decision.reason_code == reasons.SCOPE_NOT_ALLOWED


def test_policy_fails_closed_for_malformed_context() -> None:
    decision = AccessPolicyEngine().evaluate(None)

    assert decision.allowed is False
    assert decision.reason_code == reasons.MISSING_ACCESS_CONTEXT
