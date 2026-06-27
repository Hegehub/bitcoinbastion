from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
APP = ROOT / "reflex_frontend/bastion_ui/app.py"
NAV = ROOT / "reflex_frontend/bastion_ui/navigation.py"

MARKET_ROUTES = (
    "/market",
    "/market/time-machine",
    "/market/timeline",
    "/market/signals",
    "/market/evidence",
    "/market/narratives",
    "/market/sources",
)


def test_market_routes_are_registered() -> None:
    text = APP.read_text(encoding="utf-8")
    for route in MARKET_ROUTES:
        assert f'route="{route}"' in text


def test_market_command_palette_routes_exist() -> None:
    text = NAV.read_text(encoding="utf-8")
    for route in MARKET_ROUTES:
        assert route in text
    assert "Open Market Time Machine" in text
    assert "Open Market Timeline" in text
    assert "Open Market Signals" in text
    assert "Open Market Evidence" in text
    assert "Open Market Narratives" in text
    assert "Open Market Sources" in text
