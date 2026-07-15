from __future__ import annotations

from bastion_ui.routes import PUBLIC_ROUTE_SPECS
from bastion_ui.routes.registry import ALL_REFLEX_ROUTES, PUBLIC_ROUTES, STALE_ROUTES

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
    "/check",
    "/trace",
    "/trace/[report_id]",
    "/trace/[report_id]/proof-packet",
}


def test_required_public_routes_are_registered_or_in_registry() -> None:
    route_specs = {spec.route for spec in PUBLIC_ROUTE_SPECS}
    registry_routes = set(PUBLIC_ROUTES)
    assert REQUIRED_PUBLIC_ROUTES.issubset(registry_routes)
    assert route_specs.issubset(registry_routes)


def test_dynamic_trace_routes_exist() -> None:
    assert "/trace/[report_id]" in PUBLIC_ROUTES
    assert "/trace/[report_id]/proof-packet" in PUBLIC_ROUTES


def test_no_duplicate_route_declarations_exist() -> None:
    assert len(ALL_REFLEX_ROUTES) == len(set(ALL_REFLEX_ROUTES))


def test_no_stale_nextjs_only_paths_are_registered() -> None:
    assert STALE_ROUTES.isdisjoint(ALL_REFLEX_ROUTES)


def test_route_constants_match_public_route_specs_for_static_routes() -> None:
    static_public_routes = {route for route in PUBLIC_ROUTES if "[" not in route}
    assert {spec.route for spec in PUBLIC_ROUTE_SPECS}.issubset(static_public_routes)
