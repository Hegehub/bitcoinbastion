from __future__ import annotations

from typing import Literal, cast

import reflex as rx

from bastion_ui.theme.styles import BADGE
from bastion_ui.theme.tokens import (
    BASTION_DANGER,
    BASTION_INFO,
    BASTION_SUCCESS,
    BASTION_WARNING,
    RISK_HIGH,
    RISK_LOW,
    RISK_MEDIUM,
    RISK_UNKNOWN,
)

BadgeVariant = Literal[
    "neutral",
    "success",
    "warning",
    "danger",
    "info",
    "risk_low",
    "risk_medium",
    "risk_high",
    "risk_unknown",
]


def badge(label: str, variant: BadgeVariant = "neutral") -> rx.Component:
    colors = {
        "neutral": "#737373",
        "success": BASTION_SUCCESS,
        "warning": BASTION_WARNING,
        "danger": BASTION_DANGER,
        "info": BASTION_INFO,
        "risk_low": RISK_LOW,
        "risk_medium": RISK_MEDIUM,
        "risk_high": RISK_HIGH,
        "risk_unknown": RISK_UNKNOWN,
    }
    return cast(
        rx.Component,
        rx.badge(
            label,
            style={**BADGE, "border": f"1px solid {colors[variant]}", "color": colors[variant]},
        ),
    )
