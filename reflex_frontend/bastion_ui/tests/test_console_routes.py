from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
APP = ROOT / "reflex_frontend/bastion_ui/app.py"
CONSOLE_ROUTES = (
    "/console",
    "/console/trace",
    "/console/evidence",
    "/console/provider-health",
    "/console/policy",
    "/console/audit",
)
MODULE_TILES = (
    "Trace",
    "Evidence",
    "Provider Health",
    "Policy Engine",
    "Audit Log",
)


def test_console_routes_are_registered() -> None:
    text = APP.read_text(encoding="utf-8")
    for route in CONSOLE_ROUTES:
        assert f'route="{route}"' in text


def test_console_overview_module_tiles_exist() -> None:
    text = (ROOT / "reflex_frontend/bastion_ui/routes/console.py").read_text(encoding="utf-8")
    for title in MODULE_TILES:
        assert title in text
