from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

from app.api import access_dependencies

from app.domain.access.plans import PlanCode
from app.domain.access.scopes import MARKET_INTELLIGENCE_READ, METRICS_BASIC_READ
from app.services.access.plan_entitlements import build_entitlement_overlay
from app.services.access.policy_context import AccessPolicyContext
from app.services.access.policy_engine import AccessPolicyEngine


def _ctx(plan: PlanCode = PlanCode.PLUS, **overrides: object) -> AccessPolicyContext:
    overlay = build_entitlement_overlay(plan)
    data = {
        "certificate_fingerprint": "sha256:cert",
        "pass_lookup_hash": "hmac-sha256:pass",
        "plan_code": plan,
        "effective_scopes": set(overlay["allowed_scopes"]),
        "requested_scope": MARKET_INTELLIGENCE_READ,
        "session_id_hash": "hmac-sha256:session",
        "session_status": "active",
        "session_expires_at": datetime.now(UTC) + timedelta(minutes=15),
        "device_status": "active",
        "entitlement_status": "active",
        "entitlement_valid_until": datetime.now(UTC) + timedelta(days=30),
        "metric_entitlements": {"groups": overlay["metric_groups"]},
        "quota_state": {"remaining": 100},
        "revocation_state": {"allowed": True, "revoked_targets": []},
    }
    data.update(overrides)
    return AccessPolicyContext(**data)  # type: ignore[arg-type]


def test_protected_endpoint_dependency_must_call_access_policy_engine() -> None:
    source = Path("app/api/access_dependencies.py").read_text()

    assert "require_policy_decision" in source
    assert "AccessPolicyEngine" in source
    assert "evaluate" in source


def test_valid_session_without_required_scope_is_denied() -> None:
    decision = AccessPolicyEngine().evaluate(_ctx(effective_scopes={METRICS_BASIC_READ}, requested_scope=MARKET_INTELLIGENCE_READ))

    assert decision.allowed is False
    assert decision.reason_code == "scope_not_allowed"


def test_valid_session_with_revoked_pass_is_denied() -> None:
    decision = AccessPolicyEngine().evaluate(
        _ctx(revocation_state={"allowed": False, "revoked_targets": [{"target_type": "pass", "target_hash": "hmac-sha256:pass"}]})
    )

    assert decision.decision == "revoked"


def test_lower_tier_receives_upgrade_required() -> None:
    decision = AccessPolicyEngine().evaluate(_ctx(PlanCode.LITE, requested_metric_group="market.intelligence", requested_scope=None))

    assert decision.decision == "upgrade_required"
    assert decision.required_plan == PlanCode.PLUS


def test_legacy_bearer_authorization_does_not_bypass_policy() -> None:
    decision = AccessPolicyEngine().evaluate(_ctx(legacy_auth_context=True, metadata={"authorization_scheme": "Bearer"}))

    assert decision.allowed is False
    assert decision.reason_code == "legacy_auth_not_allowed"


def test_access_dependency_rejects_legacy_bearer_constant() -> None:
    assert access_dependencies.ACCESS_LEGACY_BEARER_REJECTED == "access_legacy_bearer_rejected"
