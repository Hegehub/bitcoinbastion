from __future__ import annotations

import reflex as rx

from bastion_ui.components.wow._shared import wow_card


def animated_core() -> rx.Component:
    return wow_card("Animated Core", "Lightweight optional motion placeholder.", "Animations are non-essential, local, and degrade gracefully without external network calls.")
