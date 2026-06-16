from __future__ import annotations

from typing import cast

import reflex as rx

from bastion_ui.theme.styles import INPUT

# Do not use this component to request seed phrases, private keys, wallet files,
# or signing material.


def input_field(
    label: str,
    *,
    description: str | None = None,
    placeholder: str = "",
    error: str | None = None,
    disabled: bool = False,
    required: bool = False,
) -> rx.Component:
    return cast(
        rx.Component,
        rx.vstack(
            rx.text(f"{label}{' *' if required else ''}", weight="bold"),
            rx.input(placeholder=placeholder, disabled=disabled, style=INPUT),
            rx.cond(description is not None, rx.text(description or "", color="gray")),
            rx.cond(error is not None, rx.text(error or "", color="red")),
            align="start",
            spacing="2",
        ),
    )
