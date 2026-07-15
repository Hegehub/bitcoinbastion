from __future__ import annotations

from typing import cast

import reflex as rx

from bastion_ui.accessibility.focus import SKIP_LINK_STYLE
from bastion_ui.theme.styles import PAGE


def console_layout(
    *children: rx.Component,
    sidebar: rx.Component | None = None,
    topbar: rx.Component | None = None,
    degraded_banner: rx.Component | None = None,
    audit_footer: rx.Component | None = None,
) -> rx.Component:
    return cast(
        rx.Component,
        rx.box(
            rx.link("Skip to main content", href="#main-content", style=SKIP_LINK_STYLE),
            rx.hstack(
                sidebar or rx.fragment(),
                rx.vstack(
                    topbar or rx.fragment(),
                    degraded_banner or rx.fragment(),
                    rx.box(*children, id="main-content", role="main"),
                    audit_footer or rx.fragment(),
                    width="100%",
                ),
                align="start",
            ),
            style=PAGE,
        ),
    )
