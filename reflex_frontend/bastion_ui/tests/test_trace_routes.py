from __future__ import annotations

from bastion_ui.app import PUBLIC_ROUTE_REGISTRATIONS
from bastion_ui.navigation import COMMAND_PALETTE_ACTIONS, PUBLIC_NAV_ITEMS


def test_check_and_trace_routes_are_registered() -> None:
    routes = {route for route, _page, _title in PUBLIC_ROUTE_REGISTRATIONS}
    assert "/check" in routes
    assert "/trace" in routes
    assert "/trace/[report_id]" in routes
    assert "/trace/[report_id]/proof-packet" in routes


def test_navigation_exposes_trace_and_check_command() -> None:
    nav_routes = {item.route for item in PUBLIC_NAV_ITEMS}
    command_routes = {action.route for action in COMMAND_PALETTE_ACTIONS}
    assert "/trace" in nav_routes
    assert "/trace" in command_routes
    assert "/check" in command_routes
