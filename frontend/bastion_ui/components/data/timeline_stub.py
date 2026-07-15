from __future__ import annotations

from typing import cast

import reflex as rx


def timeline_stub() -> rx.Component:
    return cast(
        rx.Component,
        rx.vstack(
            rx.text("Timeline placeholder"),
            rx.text("Future evidence-based events will appear here."),
            align="start",
        ),
    )
