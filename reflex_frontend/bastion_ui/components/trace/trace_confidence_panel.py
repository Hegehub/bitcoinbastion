from __future__ import annotations

from typing import Any

import reflex as rx

from bastion_ui.components.ui.card import card

PANEL_UNAVAILABLE = "This panel is temporarily unavailable. The Trace report remains advisory-only and may be incomplete."


def panel_card(title: str, data: dict[str, Any] | list[dict[str, Any]] | None = None) -> rx.Component:
    return card(rx.text(PANEL_UNAVAILABLE), title=title)

def trace_confidence_panel(data: dict[str, Any] | None = None) -> rx.Component:
    return panel_card("Provider Disagreement and Confidence", data)
