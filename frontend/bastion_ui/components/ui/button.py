from __future__ import annotations

from typing import Literal, cast

import reflex as rx

from bastion_ui.theme.styles import BUTTON_GHOST, BUTTON_PRIMARY, BUTTON_SECONDARY, FOCUS_RING
from bastion_ui.theme.tokens import COLOR

ButtonVariant = Literal["primary", "secondary", "ghost", "danger", "warning", "success"]


def button(
    label: str,
    variant: ButtonVariant = "primary",
    *,
    disabled: bool = False,
    loading_label: str | None = None,
) -> rx.Component:
    styles = {
        "primary": BUTTON_PRIMARY,
        "secondary": BUTTON_SECONDARY,
        "ghost": BUTTON_GHOST,
        "danger": {**BUTTON_SECONDARY, "border": f"1px solid {COLOR['error']}"},
        "warning": {**BUTTON_SECONDARY, "border": f"1px solid {COLOR['warning']}"},
        "success": {**BUTTON_SECONDARY, "border": f"1px solid {COLOR['success']}"},
    }
    return cast(
        rx.Component,
        rx.button(
            loading_label or label, disabled=disabled, style={**styles[variant], **FOCUS_RING}
        ),
    )
