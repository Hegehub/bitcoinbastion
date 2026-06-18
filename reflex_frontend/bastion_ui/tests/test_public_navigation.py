from __future__ import annotations

from bastion_ui.navigation import PUBLIC_NAV_ITEMS


def test_public_navigation_keeps_trace_visible() -> None:
    labels = {item.label for item in PUBLIC_NAV_ITEMS}
    assert "Trace" in labels


def test_public_navigation_avoids_stale_routes() -> None:
    routes = {item.route for item in PUBLIC_NAV_ITEMS}
    assert "/products" not in routes
    assert "/self-host" not in routes
