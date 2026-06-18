from __future__ import annotations

from typing import cast

import reflex as rx

from bastion_ui.navigation import CommandAction, search_command_actions
from bastion_ui.theme.styles import CARD, FOCUS_RING, INPUT

CANONICAL_PUBLIC_COMMAND_ROUTES = ("/platform", "/operations")


def command_action_row(action: CommandAction) -> rx.Component:
    return cast(
        rx.Component,
        rx.link(
            rx.vstack(
                rx.hstack(
                    rx.text(action.title, weight="bold"),
                    rx.badge(action.category, color_scheme="gray", size="1"),
                    rx.cond(
                        action.requires_input,
                        rx.badge("Requires input", color_scheme="orange", size="1"),
                        rx.fragment(),
                    ),
                    spacing="2",
                ),
                rx.text(action.route, size="2"),
                rx.text(action.description, size="2"),
                spacing="1",
                align="start",
            ),
            href=rx.cond(action.requires_input, "/trace", action.route),
            style=FOCUS_RING,
            aria_label=action.title,
        ),
    )


def command_palette_preview(query: str = "") -> rx.Component:
    actions = search_command_actions(query)
    return cast(
        rx.Component,
        rx.vstack(
            rx.text("Command Palette", weight="bold"),
            rx.input(placeholder="Search commands by title or route", value=query, style=INPUT),
            *[command_action_row(action) for action in actions],
            style=CARD,
            spacing="3",
            width="100%",
        ),
    )
