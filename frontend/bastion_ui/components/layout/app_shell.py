"""Canonical route-independent application root shared by product layouts."""

from __future__ import annotations

from typing import cast

import reflex as rx

from bastion_ui.accessibility.focus import SKIP_LINK_STYLE
from bastion_ui.components.layout.ambient import ambient_geometry
from bastion_ui.components.layout.command_palette import command_palette, global_command_shortcut
from bastion_ui.components.layout.mobile_action_dock import mobile_action_dock
from bastion_ui.components.layout.shell_context import shell_route_context
from bastion_ui.theme.styles import PAGE


def app_shell(
    *children: rx.Component,
    header: rx.Component | None = None,
    footer: rx.Component | None = None,
    complementary: rx.Component | None = None,
) -> rx.Component:
    """Own landmarks/overlays, never domain data, transports, or Access secrets."""
    return cast(
        rx.Component,
        rx.box(
            ambient_geometry(),
            global_command_shortcut(),
            rx.link("Skip to main content", href="#main-content", style=SKIP_LINK_STYLE),
            header or rx.fragment(),
            rx.hstack(
                complementary or rx.fragment(),
                rx.el.main(
                    shell_route_context(),
                    *children,
                    id="main-content",
                    aria_label="Application content",
                    width="100%",
                ),
                align="start",
                width="100%",
            ),
            footer or rx.fragment(),
            command_palette(),
            mobile_action_dock(),
            class_name="bb-content bb-app-shell",
            style=PAGE,
        ),
    )
