from __future__ import annotations

from bastion_ui.navigation import (
    CONSOLE_NAV_ITEMS,
    FOOTER_NAV_ITEMS,
    PUBLIC_NAV_ITEMS,
    STALE_CANONICAL_ROUTES,
    VALID_NAV_STATUSES,
    NavItem,
)
from bastion_ui.routes.registry import CONSOLE_ROUTES, PUBLIC_ROUTES

REQUIRED_PUBLIC = {
    "Platform": "/platform",
    "Trace": "/trace",
    "Evidence": "/evidence",
    "Status": "/status",
    "Developers": "/developers",
    "Operations": "/operations",
    "Docs": "/docs",
    "Security": "/security",
    "Roadmap": "/roadmap",
}
REQUIRED_CONSOLE_ROUTES = {
    "/console",
    "/console/trace",
    "/console/evidence",
    "/console/provider-health",
    "/console/market-intelligence",
    "/console/time-machine",
    "/console/sovereign-grid",
    "/console/policy",
    "/console/audit",
    "/console/api-explorer",
}


def labels(items: tuple[NavItem, ...]) -> set[str]:
    return {item.label for item in items}


def routes(items: tuple[NavItem, ...]) -> set[str]:
    return {item.route for item in items}


def test_public_navigation_contains_required_items_and_no_stale_routes() -> None:
    by_label = {item.label: item.route for item in PUBLIC_NAV_ITEMS}
    for label, route in REQUIRED_PUBLIC.items():
        assert by_label[label] == route
    assert STALE_CANONICAL_ROUTES.isdisjoint(routes(PUBLIC_NAV_ITEMS))


def test_footer_and_console_navigation_include_required_routes() -> None:
    assert "Trace" in labels(FOOTER_NAV_ITEMS)
    console_routes = routes(CONSOLE_NAV_ITEMS)
    assert REQUIRED_CONSOLE_ROUTES.issubset(console_routes)
    assert STALE_CANONICAL_ROUTES.isdisjoint(console_routes)


def test_navigation_routes_match_route_registry() -> None:
    public_registry = set(PUBLIC_ROUTES)
    console_registry = set(CONSOLE_ROUTES)
    assert routes(PUBLIC_NAV_ITEMS).issubset(public_registry)
    assert REQUIRED_CONSOLE_ROUTES.issubset(console_registry)
    registered_console_nav = routes(CONSOLE_NAV_ITEMS).intersection(REQUIRED_CONSOLE_ROUTES)
    assert registered_console_nav.issubset(console_registry)


def test_nav_item_routes_and_statuses_are_valid() -> None:
    for item in (*PUBLIC_NAV_ITEMS, *FOOTER_NAV_ITEMS, *CONSOLE_NAV_ITEMS):
        assert item.route.startswith("/")
        assert item.status in VALID_NAV_STATUSES
