from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
APP = ROOT / "frontend/bastion_ui/app.py"
ROUTE = ROOT / "frontend/bastion_ui/routes/console_market_intelligence.py"
NAV = ROOT / "frontend/bastion_ui/navigation.py"


def test_console_market_intelligence_route_exists() -> None:
    assert ROUTE.exists()
    assert "/console/market-intelligence" in APP.read_text(encoding="utf-8")


def test_market_intelligence_navigation_exists() -> None:
    text = NAV.read_text(encoding="utf-8")
    assert "Market Intelligence" in text
    assert "/console/market-intelligence" in text
    canonical_lines = [
        line
        for line in text.splitlines()
        if "NavItem(" in line or "CommandAction(" in line
    ]
    canonical_text = "\n".join(canonical_lines)
    assert "/products" not in canonical_text
    assert "/self-host" not in canonical_text
