from __future__ import annotations

import pytest

from bastion_ui.feature_flags import FeatureFlagId, RolloutState, resolve_flags
from bastion_ui.navigation import (
    CANONICAL_NAVIGATION,
    MOBILE_NAVIGATION,
    active_route_id,
    breadcrumb_items,
)
from bastion_ui.topology import ROUTES, RouteClass, path_for, route_enabled, validate_routes


def test_registry_has_unique_stable_id_and_path() -> None:
    validate_routes()
    assert len({route.id for route in ROUTES}) == len(ROUTES)
    assert len({route.path for route in ROUTES}) == len(ROUTES)


def test_dynamic_routes_encode_and_reject_malformed_values() -> None:
    assert path_for("trace.report", report_id="report:42") == "/trace/report%3A42"
    with pytest.raises(ValueError, match="unsafe route parameter"):
        path_for("trace.report", report_id="../private proof")
    with pytest.raises(ValueError, match="requires parameters"):
        path_for("trace.report")


def test_active_identity_and_breadcrumbs_are_registry_driven() -> None:
    assert active_route_id("/trace/report-42") == "trace.report"
    assert active_route_id("/missing") is None
    assert breadcrumb_items("trace.proof_packet") == (
        ("Bastion Trace", "/trace"),
        ("Trace Proof Packet", "/trace/[report_id]/proof-packet"),
    )


def test_mobile_is_filtered_from_shared_navigation() -> None:
    assert set(MOBILE_NAVIGATION) < set(CANONICAL_NAVIGATION)
    assert all(route.mobile_eligible for route in MOBILE_NAVIGATION)
    assert not any(
        route.route_class is RouteClass.DEVELOPMENT_ONLY for route in CANONICAL_NAVIGATION
    )


def test_flags_are_typed_fail_closed_and_not_browser_controlled() -> None:
    resolved = resolve_flags(environment="development", values={})
    assert resolved[FeatureFlagId.CORE] is RolloutState.ON
    assert (
        resolve_flags(environment="production", values={})[FeatureFlagId.WEBSOCKET_LAB]
        is RolloutState.OFF
    )
    with pytest.raises(ValueError, match="unknown frontend feature flag"):
        resolve_flags(environment="test", values={"BASTION_FLAG_UNKNOWN": "ON"})
    with pytest.raises(ValueError, match="invalid value"):
        resolve_flags(environment="test", values={"BASTION_FLAG_CORE": "maybe"})


def test_reversible_disable_does_not_change_security_metadata() -> None:
    flags = resolve_flags(environment="test", values={})
    security = next(route for route in ROUTES if route.id == "access.security_posture")
    before = security.security_requirement_id
    flags[FeatureFlagId.CORE] = RolloutState.OFF
    assert not route_enabled(security.id, flags)
    assert security.security_requirement_id == before == "access.me"


def test_payregister_is_a_separate_disabled_product() -> None:
    flags = resolve_flags(environment="production", values={})
    register_routes = [route for route in ROUTES if route.product.value == "PayRegister"]
    assert register_routes
    assert all(route.route_class is RouteClass.SEPARATE_PRODUCT for route in register_routes)
    assert all(not route_enabled(route.id, flags) for route in register_routes)
