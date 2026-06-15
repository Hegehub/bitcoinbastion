from __future__ import annotations

import reflex as rx

from bastion_ui.components.wow._shared import wow_card, wow_safety_card


def citadel_mode(content: rx.Component | None = None) -> rx.Component:
    return wow_card("Citadel Mode", "Defensive UI mode: high contrast, evidence-first, audit-first, limitations visible.", "Reduced marketing language. Degraded state visible.") if content is None else wow_safety_card("Citadel Mode Safety")
