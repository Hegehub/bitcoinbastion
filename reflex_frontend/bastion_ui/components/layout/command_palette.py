from __future__ import annotations

from typing import cast

import reflex as rx

from bastion_ui.navigation import COMMAND_PALETTE_ACTIONS, CommandAction
from bastion_ui.state.command_palette_state import CommandPaletteState

CANONICAL_PUBLIC_ROUTES = ("/platform", "/operations")


def command_palette_trigger() -> rx.Component:
    return cast(
        rx.Component,
        rx.button(
            "Command",
            on_click=CommandPaletteState.toggle_open,
            aria_label="Open command palette",
        ),
    )


def _action_row(action: CommandAction) -> rx.Component:
    status = "requires input" if action.requires_input else action.status.replace("_", " ")
    return cast(
        rx.Component,
        rx.box(
            rx.hstack(rx.text(action.title, weight="bold"), rx.badge(status), justify="between"),
            rx.text(action.route),
            rx.text(action.description),
            rx.cond(action.safety_note is not None, rx.text(action.safety_note or "")),
            padding="12px",
            border="1px solid #2A2A2A",
            border_radius="12px",
        ),
    )


def command_palette() -> rx.Component:
    return cast(
        rx.Component,
        rx.box(
            rx.vstack(
                rx.heading("Command palette", size="4"),
                rx.input(
                    placeholder="Search actions",
                    value=CommandPaletteState.query,
                    on_change=CommandPaletteState.set_query,
                ),
                *[_action_row(action) for action in COMMAND_PALETTE_ACTIONS],
                align="start",
                spacing="3",
            ),
            display=rx.cond(CommandPaletteState.open, "block", "none"),
        ),
    )
