from __future__ import annotations

from typing import cast

import reflex as rx


def evidence_list_stub() -> rx.Component:
    return cast(
        rx.Component,
        rx.vstack(
            rx.text("Evidence placeholder"),
            rx.text("Limited evidence and provider context will appear here."),
            align="start",
        ),
    )
