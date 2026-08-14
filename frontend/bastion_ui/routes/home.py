from __future__ import annotations

import reflex as rx

from bastion_ui.components.operations.screens import overview_cockpit
from bastion_ui.routes._shared import public_page


def home_page() -> rx.Component:
    return public_page(
        "Bitcoin Bastion Overview",
        overview_cockpit(),
        subtitle="Current operational facts from authoritative Bitcoin Bastion APIs.",
    )
