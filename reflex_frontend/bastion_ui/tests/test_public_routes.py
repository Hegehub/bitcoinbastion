from __future__ import annotations

from bastion_ui.app import PUBLIC_ROUTE_REGISTRATIONS

REQUIRED_PUBLIC_ROUTES = {
    "/",
    "/platform",
    "/developers",
    "/operations",
    "/manifesto",
    "/evidence",
    "/status",
    "/roadmap",
    "/security",
    "/docs",
}


def test_all_public_static_routes_are_registered() -> None:
    routes = {route for route, _page, _title in PUBLIC_ROUTE_REGISTRATIONS}
    assert REQUIRED_PUBLIC_ROUTES <= routes


def test_trace_routes_are_registered_without_console_cutover() -> None:
    routes = {route for route, _page, _title in PUBLIC_ROUTE_REGISTRATIONS}
    assert "/check" in routes
    assert "/trace/[report_id]" in routes
    assert "/trace/[report_id]/proof-packet" in routes
