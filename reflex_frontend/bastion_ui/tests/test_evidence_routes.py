from __future__ import annotations

from bastion_ui.app import PUBLIC_ROUTE_REGISTRATIONS
from bastion_ui.routes.evidence import evidence_page


def test_evidence_route_exists() -> None:
    routes = {route for route, _, _ in PUBLIC_ROUTE_REGISTRATIONS}
    assert "/evidence" in routes
    assert evidence_page is not None
