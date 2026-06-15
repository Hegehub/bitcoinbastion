from __future__ import annotations

import reflex as rx

from bastion_ui.components.wow._shared import wow_safety_card


def no_custody_safety_layer() -> rx.Component:
    return wow_safety_card()
