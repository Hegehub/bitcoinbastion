from __future__ import annotations

from pathlib import Path

from bastion_ui.routes.registry import MARKET_ROUTES

ROOT = Path(__file__).resolve().parents[3]
APP = ROOT / "frontend/bastion_ui/app.py"
NAV = ROOT / "frontend/bastion_ui/navigation.py"

REQUIRED_MARKET_ROUTES = (
    "/market",
    "/market/time-machine",
    "/market/timeline",
    "/market/signals",
    "/market/evidence",
    "/market/narratives",
    "/market/sources",
)


def test_market_routes_are_registered_or_explicitly_delegated() -> None:
    text = APP.read_text(encoding="utf-8")
    for route in REQUIRED_MARKET_ROUTES:
        metadata = MARKET_ROUTES[route]
        assert metadata["status"] in {"implemented", "delegated"}
        if metadata["status"] == "implemented":
            assert metadata["owner"] == "reflex"
            assert f'route="{route}"' in text


def test_market_command_palette_routes_exist() -> None:
    text = NAV.read_text(encoding="utf-8")
    for route in REQUIRED_MARKET_ROUTES:
        assert route in text
    assert "Open Market Time Machine" in text
    assert "Open Market Timeline" in text
    assert "Open Market Signals" in text
    assert "Open Market Evidence" in text
    assert "Open Market Narratives" in text
    assert "Open Market Sources" in text


def test_market_routes_do_not_claim_production_replacement_or_financial_advice() -> None:
    market_files = [
        ROOT / "frontend/bastion_ui/routes/market.py",
        ROOT / "frontend/bastion_ui/routes/market_time_machine.py",
        ROOT / "frontend/bastion_ui/components/market/market_safety_banner.py",
        ROOT / "frontend/bastion_ui/components/console/market_intelligence_panel.py",
    ]
    text = "\n".join(path.read_text(encoding="utf-8") for path in market_files).lower()
    assert "production replacement" not in text
    assert "financial advice" in text
    assert "not financial advice" in text or "informational only" in text
