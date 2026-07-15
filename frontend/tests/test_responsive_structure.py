from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_responsive_helpers_exist() -> None:
    text = (ROOT / "bastion_ui/components/layout/responsive.py").read_text()
    assert "WRAP_LONG_TEXT" in text
    assert "overflow_wrap" in text
    assert "RESPONSIVE_TABLE_WRAPPER" in text


def test_mobile_navigation_contains_required_routes_without_stale_links() -> None:
    text = (ROOT / "bastion_ui/components/layout/mobile_nav.py").read_text()
    assert "Check Bitcoin Address" in text
    assert "Console" in text
    assert "/products" not in text
    assert "/self-host" not in text


def test_console_layout_has_mobile_fallback_structure() -> None:
    text = (ROOT / "bastion_ui/components/layout/console_layout.py").read_text()
    assert "sidebar" in text
    assert "main-content" in text
