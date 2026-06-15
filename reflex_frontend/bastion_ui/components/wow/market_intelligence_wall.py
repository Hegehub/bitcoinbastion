from __future__ import annotations

import reflex as rx

from bastion_ui.components.wow._shared import wow_card


def market_intelligence_wall() -> rx.Component:
    return wow_card("Market Intelligence Wall", "latest events: preview", "shock/narrative preview: backend required", "provider health state: unknown", "confidence: unknown", "Not financial advice.", "Correlation is not proof of causation.")
