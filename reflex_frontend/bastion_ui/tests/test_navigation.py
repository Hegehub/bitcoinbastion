from __future__ import annotations

from bastion_ui.navigation import (
    CONSOLE_NAV_ITEMS,
    FOOTER_NAV_ITEMS,
    PUBLIC_NAV_ITEMS,
    STALE_CANONICAL_ROUTES,
    VALID_NAV_STATUSES,
    NavItem,
)

REQUIRED_PUBLIC = [
    "Platform",
    "Trace",
    "Evidence",
    "Status",
    "Developers",
    "Operations",
    "Docs",
    "Security",
    "Roadmap",
]
REQUIRED_CONSOLE = [
    "Dashboard",
    "Trace",
    "Evidence",
    "Provider Health",
    "Market Intelligence",
    "Time Machine",
    "Sovereign Grid",
    "Policy Engine",
    "Audit Log",
    "Deployment Status",
    "API Explorer",
]


def labels(items: tuple[NavItem, ...]) -> set[str]:
    return {item.label for item in items}


def routes(items: tuple[NavItem, ...]) -> set[str]:
    return {item.route for item in items}


def test_public_navigation_contains_required_items_and_no_stale_routes() -> None:
    public_labels = labels(PUBLIC_NAV_ITEMS)
    for label in REQUIRED_PUBLIC:
        assert label in public_labels
    assert STALE_CANONICAL_ROUTES.isdisjoint(routes(PUBLIC_NAV_ITEMS))


def test_footer_and_console_navigation() -> None:
    assert "Trace" in labels(FOOTER_NAV_ITEMS)
    console_labels = labels(CONSOLE_NAV_ITEMS)
    for label in REQUIRED_CONSOLE:
        assert label in console_labels


def test_nav_item_routes_and_statuses_are_valid() -> None:
    for item in (*PUBLIC_NAV_ITEMS, *FOOTER_NAV_ITEMS, *CONSOLE_NAV_ITEMS):
        if item.status == "active":
            assert item.route
        assert item.status in VALID_NAV_STATUSES
