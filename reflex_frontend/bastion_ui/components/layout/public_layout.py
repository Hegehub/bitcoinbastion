from __future__ import annotations

from typing import cast

import reflex as rx

from bastion_ui.components.layout.container import container
from bastion_ui.theme.styles import PAGE


def public_layout(
    *children: rx.Component,
    header: rx.Component | None = None,
    footer: rx.Component | None = None,
    safety_notice: rx.Component | None = None,
) -> rx.Component:
    return cast(
        rx.Component,
        rx.box(
            header or rx.fragment(),
            rx.box(container(safety_notice or rx.fragment(), *children), id="main-content"),
            footer or rx.fragment(),
            style=PAGE,
        ),
    )
