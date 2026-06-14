from __future__ import annotations

from typing import Literal, cast

import reflex as rx

from bastion_ui.components.ui.badge import badge
from bastion_ui.theme.styles import CARD

AlertVariant = Literal["info", "warning", "danger", "success"]


def alert(message: str, variant: AlertVariant = "info", title: str | None = None) -> rx.Component:
    label = title or variant.upper()
    return cast(rx.Component, rx.box(badge(label, "neutral" if variant == "info" else variant), rx.text(message), style=CARD))
