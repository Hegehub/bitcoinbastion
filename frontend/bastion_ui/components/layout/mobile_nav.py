from __future__ import annotations

from typing import cast

import reflex as rx

from bastion_ui.components.layout.command_palette import command_palette_trigger
from bastion_ui.navigation import MOBILE_NAVIGATION, TRACE_SAFETY_NOTE
from bastion_ui.state.navigation_state import NavigationState
from bastion_ui.topology import path_for


def mobile_nav_trigger() -> rx.Component:
    return cast(
        rx.Component,
        rx.button(
            "Menu",
            id="mobile-navigation-trigger",
            on_click=NavigationState.toggle_mobile_nav,
            aria_label="Open mobile navigation",
            aria_controls="mobile-navigation",
            aria_expanded=NavigationState.mobile_nav_open,
        ),
    )


def mobile_nav() -> rx.Component:
    return cast(
        rx.Component,
        rx.vstack(
            rx.text("Mobile navigation"),
            rx.button(
                "Close menu",
                id="mobile-navigation-close",
                on_click=NavigationState.set_mobile_nav_open(False),  # type: ignore[arg-type,call-arg]
                aria_label="Close mobile navigation",
            ),
            *[
                rx.link(
                    item.title,
                    href=path_for(item.id),
                    on_click=NavigationState.set_mobile_nav_open(False),  # type: ignore[arg-type,call-arg]
                    aria_current=rx.cond(
                        NavigationState.current_path == path_for(item.id), "page", None
                    ),
                )
                for item in MOBILE_NAVIGATION
            ],
            command_palette_trigger(
                trigger_id="mobile-navigation-command-trigger", label="Open command palette"
            ),
            rx.text(TRACE_SAFETY_NOTE),
            align="start",
            spacing="3",
            id="mobile-navigation",
            role="navigation",
            aria_label="Mobile navigation",
            display=rx.cond(NavigationState.mobile_nav_open, "flex", "none"),
            position="fixed",
            inset="0",
            padding=(
                "max(20px, env(safe-area-inset-top)) 20px max(20px, env(safe-area-inset-bottom))"
            ),
            overflow_y="auto",
            z_index="35",
            class_name="bb-glass bb-shell-overlay",
        ),
    )
