from __future__ import annotations

from pathlib import Path

from bastion_ui.navigation import CONSOLE_NAV_ITEMS
from bastion_ui.routes.registry import CONSOLE_ROUTES

ROOT = Path(__file__).resolve().parents[3]
APP = ROOT / "reflex_frontend/bastion_ui/app.py"
REQUIRED_CONSOLE_ROUTES = (
    "/console",
    "/console/trace",
    "/console/evidence",
    "/console/market-intelligence",
    "/console/time-machine",
    "/console/sovereign-grid",
    "/console/provider-health",
    "/console/policy",
    "/console/audit",
    "/console/api-explorer",
)
MODULE_TILES = (
    "Trace",
    "Evidence",
    "Provider Health",
    "Market Intelligence",
    "Time Machine",
    "Sovereign Grid",
    "Policy Engine",
    "Audit Log",
)
RISKY_ROUTE_PARTS = ("/execute", "/sign", "/broadcast", "/auto-approve")


def test_console_routes_are_registered() -> None:
    text = APP.read_text(encoding="utf-8")
    for route in REQUIRED_CONSOLE_ROUTES:
        assert route in CONSOLE_ROUTES
        assert f'route="{route}"' in text


def test_console_routes_match_navigation_entries() -> None:
    nav_routes = {item.route for item in CONSOLE_NAV_ITEMS}
    for route in REQUIRED_CONSOLE_ROUTES:
        assert route in nav_routes


def test_console_overview_module_tiles_exist() -> None:
    text = (ROOT / "reflex_frontend/bastion_ui/routes/console.py").read_text(encoding="utf-8")
    for title in MODULE_TILES:
        assert title in text


def test_console_routes_are_not_risky_execution_routes() -> None:
    all_routes = "\n".join(CONSOLE_ROUTES).lower()
    for route_part in RISKY_ROUTE_PARTS:
        assert route_part not in all_routes


def test_policy_console_uses_review_or_advisory_language() -> None:
    path = ROOT / "reflex_frontend/bastion_ui/components/console/policy_console_panel.py"
    text = path.read_text(encoding="utf-8")
    normalized = text.lower()
    assert "review" in normalized or "advisory" in normalized
    assert "direct treasury execution" not in normalized
