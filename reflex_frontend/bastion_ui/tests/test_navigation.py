from __future__ import annotations

from bastion_ui.navigation import (
    CONSOLE_NAV_ITEMS,
    FOOTER_NAV_ITEMS,
    PUBLIC_NAV_ITEMS,
    VALID_NAV_STATUSES,
)

REQUIRED_PUBLIC_LABELS = {
    "Platform",
    "Trace",
    "Evidence",
    "Status",
    "Developers",
    "Operations",
    "Docs",
    "Security",
    "Roadmap",
}

REQUIRED_CONSOLE_LABELS = {
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
}


def test_public_navigation_contains_required_routes() -> None:
    labels = {item.label for item in PUBLIC_NAV_ITEMS}
    assert REQUIRED_PUBLIC_LABELS <= labels
    assert [item.label for item in PUBLIC_NAV_ITEMS][:3] == ["Platform", "Trace", "Evidence"]


def test_public_navigation_avoids_stale_canonical_routes() -> None:
    routes = {item.route for item in PUBLIC_NAV_ITEMS}
    assert "/products" not in routes
    assert "/self-host" not in routes


def test_footer_navigation_contains_trace() -> None:
    assert "Trace" in {item.label for item in FOOTER_NAV_ITEMS}


def test_console_navigation_contains_required_modules() -> None:
    assert REQUIRED_CONSOLE_LABELS <= {item.label for item in CONSOLE_NAV_ITEMS}


def test_every_active_navigation_item_has_route_and_valid_status() -> None:
    for item in (*PUBLIC_NAV_ITEMS, *FOOTER_NAV_ITEMS, *CONSOLE_NAV_ITEMS):
        assert item.status in VALID_NAV_STATUSES
        if item.status == "active":
            assert item.route


def test_trace_and_evidence_navigation_have_safety_notes() -> None:
    safety_by_label = {item.label: item.safety_note for item in PUBLIC_NAV_ITEMS}
    assert safety_by_label["Trace"]
    assert safety_by_label["Evidence"]
