from __future__ import annotations

from bastion_ui.navigation import CONSOLE_NAV_ITEMS


def test_console_sidebar_navigation_includes_core_modules() -> None:
    routes = {item.route for item in CONSOLE_NAV_ITEMS}
    assert "/console/trace" in routes
    assert "/console/evidence" in routes
    assert "/console/provider-health" in routes
    assert "/console/policy" in routes
    assert "/console/audit" in routes


def test_advanced_console_modules_are_preview_routes() -> None:
    status_by_route = {item.route: item.status for item in CONSOLE_NAV_ITEMS}
    assert status_by_route["/console/time-machine"] == "preview"
    assert status_by_route["/console/sovereign-grid"] == "preview"
    assert status_by_route["/console/api-explorer"] == "preview"
