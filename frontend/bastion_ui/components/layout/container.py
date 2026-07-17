from __future__ import annotations

from typing import cast

import reflex as rx


def container(*children: rx.Component) -> rx.Component:
    return cast(
        rx.Component,
        rx.container(
            *children,
            size="4",
            width="100%",
            padding="24px",
        ),
    )
