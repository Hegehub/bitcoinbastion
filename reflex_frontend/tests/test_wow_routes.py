from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_console_wow_route_exists() -> None:
    app = (ROOT / "bastion_ui/app.py").read_text(encoding="utf-8")
    assert 'route="/console/wow"' in app


def test_wow_navigation_exists() -> None:
    nav = (ROOT / "bastion_ui/navigation.py").read_text(encoding="utf-8")
    assert "/console/wow" in nav
    assert "Open Wow Layer" in nav
