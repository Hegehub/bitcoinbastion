from __future__ import annotations

from typing import Literal, cast

import reflex as rx

from bastion_ui.theme.styles import BUTTON_GHOST, BUTTON_PRIMARY, BUTTON_SECONDARY, FOCUS_RING
from bastion_ui.theme.tokens import BASTION_DANGER, BASTION_SUCCESS, BASTION_WARNING

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
        "danger": {**BUTTON_SECONDARY, "border": f"1px solid {BASTION_DANGER}"},
        "warning": {**BUTTON_SECONDARY, "border": f"1px solid {BASTION_WARNING}"},
        "success": {**BUTTON_SECONDARY, "border": f"1px solid {BASTION_SUCCESS}"},
    }
    text = loading_label if loading_label else label
    return cast(
        rx.Component,
        rx.button(text, disabled=disabled, style={**styles[variant], **FOCUS_RING}),
    )
