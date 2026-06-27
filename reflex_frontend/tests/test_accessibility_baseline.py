from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_layouts_have_skip_to_content_and_main_role() -> None:
    public_layout = (ROOT / "bastion_ui/components/layout/public_layout.py").read_text()
    console_layout = (ROOT / "bastion_ui/components/layout/console_layout.py").read_text()
    assert "Skip to main content" in public_layout
    assert "Skip to main content" in console_layout
    assert 'role="main"' in public_layout
    assert 'role="main"' in console_layout


def test_navigation_and_command_palette_labels_exist() -> None:
    mobile = (ROOT / "bastion_ui/components/layout/mobile_nav.py").read_text()
    palette = (ROOT / "bastion_ui/components/layout/command_palette.py").read_text()
    assert 'aria_label="Mobile navigation"' in mobile
    assert 'aria_controls="mobile-navigation"' in mobile
    assert "aria_expanded" in mobile
    assert 'aria_label="Command palette"' in palette
    assert "Search command palette actions" in palette


def test_trace_input_has_label_and_help_text() -> None:
    text = (ROOT / "bastion_ui/components/trace/address_input.py").read_text()
    assert "trace-address-label" in text
    assert "trace-address-help" in text
    assert "aria_describedby" in text
