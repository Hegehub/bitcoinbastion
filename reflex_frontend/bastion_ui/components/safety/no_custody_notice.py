from __future__ import annotations

from typing import cast

import reflex as rx


def no_custody_notice() -> rx.Component:
    return cast(
        rx.Component,
        rx.vstack(
            rx.text("No custody.", weight="bold"),
            rx.text("Public Bitcoin addresses only."),
            rx.text("Never enter seed phrases, private keys, wallet files or signing material."),
            align="start",
        ),
    )
