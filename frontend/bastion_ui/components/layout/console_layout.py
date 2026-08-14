from __future__ import annotations

import reflex as rx

from bastion_ui.components.layout.app_shell import app_shell


def console_layout(
    *children: rx.Component,
    sidebar: rx.Component | None = None,
    topbar: rx.Component | None = None,
    degraded_banner: rx.Component | None = None,
    audit_footer: rx.Component | None = None,
) -> rx.Component:
    return app_shell(
        rx.vstack(
            topbar or rx.fragment(),
            degraded_banner or rx.fragment(),
            *children,
            audit_footer or rx.fragment(),
            width="100%",
        ),
        complementary=sidebar,
    )
