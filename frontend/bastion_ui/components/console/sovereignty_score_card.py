from __future__ import annotations

import reflex as rx

from bastion_ui.components.ui.badge import badge
from bastion_ui.components.ui.card import card


def sovereignty_score_card() -> rx.Component:
    return card(
        rx.text(
            
                "Sovereignty score is unavailable until backend status exposes "
                "sanitized readiness data."
            
        ),
        rx.text("No frontend-estimated score is shown to avoid implying security certification."),
        title="Sovereignty score",
        badge=badge("unknown", "warning"),
        variant="console",
    )
