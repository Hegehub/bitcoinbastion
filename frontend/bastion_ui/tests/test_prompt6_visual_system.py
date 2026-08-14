from __future__ import annotations

from pathlib import Path

import reflex as rx

from bastion_ui.components.data.provenance_badge import provenance_badge
from bastion_ui.components.ui.card import card
from bastion_ui.domain.provenance import ProvenanceState
from bastion_ui.theme.materials import MATERIALS, material_style
from bastion_ui.theme.tokens import COLOR, DARK, LIGHT, MaterialLevel
from bastion_ui.theme.validation import (
    canonical_blue_audit,
    contrast,
    validate_visual_system,
    visual_inventory,
)

ROOT = Path(__file__).resolve().parents[1]


def test_palettes_materials_and_contrast_are_complete() -> None:
    validate_visual_system()
    assert DARK.brand == "#F7931A"
    assert LIGHT.brand != LIGHT.warning
    assert contrast(DARK.text, DARK.background) >= 7
    assert contrast(LIGHT.text, LIGHT.background) >= 7
    assert set(MATERIALS) == set(MaterialLevel)


def test_glass_is_bounded_and_matte_has_no_blur() -> None:
    assert "backdrop_filter" not in material_style(MaterialLevel.MATTE)
    assert sum("backdrop_filter" in style for style in MATERIALS.values()) == 3


def test_no_blue_brand_bypass_in_canonical_visual_system() -> None:
    assert canonical_blue_audit(ROOT / "theme") == ()
    assert COLOR["brand"] != "#3B82F6"


def test_provenance_remains_exactly_four_text_first_states() -> None:
    assert {state.value for state in ProvenanceState} == {
        "LIVE",
        "VERIFIED_SNAPSHOT",
        "DEMO_FIXTURE",
        "UNAVAILABLE",
    }
    component = provenance_badge("LIVE", source="Backend")
    assert isinstance(component, rx.Component)


def test_shared_card_material_variants_render() -> None:
    for variant in ("default", "matte", "glass", "elevated", "safety"):
        assert isinstance(card(rx.text("Readable"), variant=variant), rx.Component)


def test_visual_cost_inventory_is_bounded() -> None:
    inventory = visual_inventory(ROOT)
    assert inventory["backdrop_filters"] <= 8
    assert inventory["animations"] <= 12


def test_accessibility_media_fallbacks_and_client_theme_toggle_exist() -> None:
    css = (ROOT.parents[0] / "assets" / "visual-system.css").read_text()
    assert "prefers-reduced-motion:reduce" in css
    assert "prefers-reduced-transparency:reduce" in css
    assert "forced-colors:active" in css
    header = (ROOT / "components/layout/header.py").read_text()
    assert "rx.toggle_color_mode" in header
    assert "SecurityShellState" not in header
    assert "WebSocketLabState" not in header
    assert "Prompt2StatusState" not in header
