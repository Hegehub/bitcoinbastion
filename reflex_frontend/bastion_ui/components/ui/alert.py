from __future__ import annotations

from typing import Literal, cast

import reflex as rx

from bastion_ui.theme.styles import SAFETY_CARD

AlertVariant = Literal["info", "success", "warning", "danger", "degraded", "stale", "advisory"]

ALERT_LABELS = {
    "info": "Advisory",
    "success": "Available",
    "warning": "Manual review recommended",
    "danger": "Limited evidence",
    "degraded": "Degraded",
    "stale": "Stale data",
    "advisory": "Advisory",
}


def alert(message: str, variant: AlertVariant = "info") -> rx.Component:
    return cast(
        rx.Component,
        rx.box(rx.text(ALERT_LABELS[variant], weight="bold"), rx.text(message), style=SAFETY_CARD),
    )
