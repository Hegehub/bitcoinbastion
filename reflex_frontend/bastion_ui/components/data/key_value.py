from __future__ import annotations

from typing import cast

import reflex as rx


def key_value(label: str, value: str) -> rx.Component:
    return cast(
        rx.Component,
        rx.hstack(rx.text(label, color="#A3A3A3"), rx.text(value), justify="between", width="100%"),
    )
