from __future__ import annotations

import pytest

pytest.importorskip("reflex")

from bastion_ui.routes import PUBLIC_ROUTE_SPECS

REQUIRED_ROUTES = {
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


def test_public_static_routes_are_registered() -> None:
    routes = {spec.route for spec in PUBLIC_ROUTE_SPECS}
    assert REQUIRED_ROUTES.issubset(routes)


def test_public_route_specs_have_titles_and_callables() -> None:
    for spec in PUBLIC_ROUTE_SPECS:
        assert spec.title
        assert callable(spec.page)
