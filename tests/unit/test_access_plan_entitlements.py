from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.domain.access.plans import PlanCode
from app.services.access.plan_entitlements import (
    build_entitlement_overlay,
    build_metric_catalog_response,
    get_plan_limits,
    get_plan_metric_groups,
    is_metric_allowed,
    is_metric_group_allowed,
    required_plan_for_metric,
    required_plan_for_metric_group,
    validate_history_range_allowed,
    validate_interval_allowed,
)


def test_plan_metric_group_access_matrix() -> None:
    assert is_metric_group_allowed(PlanCode.LITE, "market.basic") is True
    assert is_metric_group_allowed(PlanCode.LITE, "market.intelligence") is False
    assert is_metric_group_allowed(PlanCode.LITE, "signals.advanced") is False
    assert is_metric_group_allowed(PlanCode.BASIC, "bitcoin.network") is True
    assert is_metric_group_allowed(PlanCode.BASIC, "market.intelligence") is False
    assert is_metric_group_allowed(PlanCode.PLUS, "market.intelligence") is True
    assert is_metric_group_allowed(PlanCode.PLUS, "signals.advanced") is False
    assert is_metric_group_allowed(PlanCode.PLUS, "trace.advanced") is False
    assert is_metric_group_allowed(PlanCode.PRO, "signals.advanced") is True
    assert is_metric_group_allowed(PlanCode.PRO, "trace.advanced") is True
    assert is_metric_group_allowed(PlanCode.PRO, "treasury.read") is True
    assert is_metric_group_allowed(PlanCode.BUSINESS, "payregister.metrics") is True
    assert is_metric_group_allowed(PlanCode.ENTERPRISE, "enterprise.custom") is True


def test_metric_access_and_unknown_rejection() -> None:
    assert is_metric_allowed(PlanCode.LITE, "btc.price") is True
    assert is_metric_allowed(PlanCode.PLUS, "bastion.signal.advanced") is False
    assert is_metric_allowed(PlanCode.PRO, "bastion.signal.advanced") is True

    with pytest.raises(ValueError, match="unknown_metric"):
        is_metric_allowed(PlanCode.ENTERPRISE, "unknown.metric")
    with pytest.raises(ValueError, match="unknown_metric_group"):
        is_metric_group_allowed(PlanCode.ENTERPRISE, "unknown.group")


def test_required_plan_helpers_return_minimum_correct_plan() -> None:
    assert required_plan_for_metric("btc.price") is PlanCode.LITE
    assert required_plan_for_metric("btc.volatility.regime") is PlanCode.PLUS
    assert required_plan_for_metric("bastion.signal.advanced") is PlanCode.PRO
    assert required_plan_for_metric("payregister.operator_audit") is PlanCode.BUSINESS
    assert required_plan_for_metric("enterprise.custom.audit_export") is PlanCode.ENTERPRISE

    assert required_plan_for_metric_group("market.basic") is PlanCode.LITE
    assert required_plan_for_metric_group("market.intelligence") is PlanCode.PLUS
    assert required_plan_for_metric_group("trace.advanced") is PlanCode.PRO
    assert required_plan_for_metric_group("payregister.metrics") is PlanCode.BUSINESS
    assert required_plan_for_metric_group("enterprise.custom") is PlanCode.ENTERPRISE


def test_interval_and_history_range_validation() -> None:
    assert validate_interval_allowed(PlanCode.LITE, "1h") is True
    assert validate_interval_allowed(PlanCode.LITE, "15m") is False
    assert validate_interval_allowed(PlanCode.PLUS, "5m") is True
    assert validate_interval_allowed(PlanCode.PLUS, "1m") is False
    assert validate_interval_allowed(PlanCode.PRO, "1m") is True

    assert validate_history_range_allowed(PlanCode.LITE, 30) is True
    assert validate_history_range_allowed(PlanCode.LITE, 31) is False
    assert validate_history_range_allowed(PlanCode.ENTERPRISE, 10_000) is True


def test_no_plan_includes_broad_all_access_scope() -> None:
    forbidden = {"metrics:all", "api:all", "admin:all"}

    for plan in PlanCode:
        overlay = build_entitlement_overlay(plan)
        assert set(overlay["allowed_scopes"]).isdisjoint(forbidden)
        assert get_plan_metric_groups(plan)


def test_metric_catalog_response_includes_locked_metric_groups() -> None:
    response = build_metric_catalog_response(PlanCode.LITE)
    locked_codes = {locked["group_code"] for locked in response["locked_metric_groups"]}

    assert response["plan"] == PlanCode.LITE.value
    assert "market.intelligence" in locked_codes
    assert "enterprise.custom" in locked_codes


def test_entitlement_overlay_is_stable_and_json_serializable() -> None:
    overlay = build_entitlement_overlay(PlanCode.PRO)

    assert overlay == build_entitlement_overlay(PlanCode.PRO)
    assert json.loads(json.dumps(overlay))["plan_code"] == PlanCode.PRO.value


def test_business_and_enterprise_custom_values_are_represented_safely() -> None:
    business_limits = get_plan_limits(PlanCode.BUSINESS)
    enterprise_limits = get_plan_limits(PlanCode.ENTERPRISE)

    assert business_limits.child_api_keys == "role_based"
    assert enterprise_limits.requests_per_minute is None
    assert enterprise_limits.child_api_keys == "custom"
    assert enterprise_limits.offline_validity_pack == "custom_policy"


def test_modules_do_not_import_legacy_auth_dependencies() -> None:
    files = [
        Path("app/services/access/metric_catalog.py"),
        Path("app/services/access/metric_costs.py"),
        Path("app/services/access/plan_entitlements.py"),
    ]
    source = "\n".join(path.read_text() for path in files)

    assert "AuthService" not in source
    assert "UserRepository" not in source
