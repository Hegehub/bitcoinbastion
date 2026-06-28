from __future__ import annotations

import reflex as rx

from bastion_ui.components.ui.card import card
from bastion_ui.components.ui.safety_banner import safety_banner


def source_disagreement_panel() -> rx.Component:
    return card(
        safety_banner("provider_disagreement"),
        rx.text("Evidence sources do not fully agree."),
        rx.text("Some providers returned incomplete or stale data."),
        rx.text("Manual review is recommended."),
        title="Provider disagreement",
        variant="safety",
    )
