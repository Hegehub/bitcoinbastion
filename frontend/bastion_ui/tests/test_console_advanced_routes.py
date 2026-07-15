from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
APP = ROOT / "frontend/bastion_ui/app.py"
ADVANCED_ROUTES = (
    "/console/market-intelligence",
    "/console/time-machine",
    "/console/sovereign-grid",
    "/console/api-explorer",
)


def test_advanced_console_routes_are_registered() -> None:
    text = APP.read_text(encoding="utf-8")
    for route in ADVANCED_ROUTES:
        assert f'route="{route}"' in text


def test_sidebar_and_command_palette_include_advanced_modules() -> None:
    text = (ROOT / "frontend/bastion_ui/navigation.py").read_text(encoding="utf-8")
    for route in ADVANCED_ROUTES:
        assert route in text
    assert '"/products", "console"' not in text
    assert '"/self-host", "console"' not in text
