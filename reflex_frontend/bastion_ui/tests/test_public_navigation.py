from __future__ import annotations

from bastion_ui.navigation import PUBLIC_NAV_ITEMS, STALE_CANONICAL_ROUTES


def test_public_navigation_contains_trace_and_avoids_stale_routes() -> None:
    labels = {item.label for item in PUBLIC_NAV_ITEMS}
    routes = {item.route for item in PUBLIC_NAV_ITEMS}
    assert "Trace" in labels
    assert STALE_CANONICAL_ROUTES.isdisjoint(routes)
