from __future__ import annotations

from typing import cast

import reflex as rx

from bastion_ui.components.ui.badge import badge


def console_topbar() -> rx.Component:
    return cast(
        rx.Component,
        rx.hstack(
            rx.heading("Bastion Console", size="5"),
            badge("Environment: unknown", "info"),
            badge("API: unknown", "warning"),
            badge("Runtime: unknown", "info"),
            rx.spacer(),
            rx.link("Public site", href="/"),
            rx.link("Docs", href="/docs"),
            width="100%",
            align="center",
            spacing="4",
            wrap="wrap",
        ),
    )
