from __future__ import annotations

from typing import Literal, cast

import reflex as rx

from bastion_ui.theme.styles import CARD
from bastion_ui.theme.tokens import BASTION_DANGER, BASTION_INFO, BASTION_SUCCESS, BASTION_WARNING

AlertVariant = Literal["info", "success", "warning", "danger", "degraded", "stale", "advisory"]

ALERT_LABELS: dict[AlertVariant, str] = {
    "info": "Advisory",
    "success": "Available",
    "warning": "Manual review recommended",
    "danger": "Limited evidence",
    "degraded": "Degraded",
    "stale": "Stale data",
    "advisory": "Advisory",
}


def alert(message: str, variant: AlertVariant = "info") -> rx.Component:
    colors = {
        "info": BASTION_INFO,
        "success": BASTION_SUCCESS,
        "warning": BASTION_WARNING,
        "danger": BASTION_DANGER,
        "degraded": BASTION_WARNING,
        "stale": BASTION_WARNING,
        "advisory": BASTION_INFO,
    }
    return cast(
        rx.Component,
        rx.box(
            rx.vstack(
                rx.text(ALERT_LABELS[variant], weight="bold"),
                rx.text(message),
                align="start",
            ),
            style={**CARD, "border": f"1px solid {colors[variant]}"},
        ),
    )
