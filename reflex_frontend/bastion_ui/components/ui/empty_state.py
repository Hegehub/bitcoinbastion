from __future__ import annotations

from typing import cast

import reflex as rx


def empty_state(title: str, description: str, action: rx.Component | None = None) -> rx.Component:
    return cast(
        rx.Component,
        rx.center(
            rx.vstack(
                rx.heading(title, size="4"),
                rx.text(description),
                action or rx.fragment(),
                align="center",
            ),
            padding="32px",
        ),
    )
