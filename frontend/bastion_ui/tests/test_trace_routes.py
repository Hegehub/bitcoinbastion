from __future__ import annotations

import pytest

pytest.importorskip("reflex")

from bastion_ui.routes import PUBLIC_ROUTE_SPECS


def test_check_and_trace_routes_exist() -> None:
    routes = {spec.route for spec in PUBLIC_ROUTE_SPECS}
    assert "/check" in routes
    assert "/trace" in routes
