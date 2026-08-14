from __future__ import annotations

from typing import cast

import reflex as rx

from bastion_ui.components.layout.command_palette import command_palette_trigger
from bastion_ui.theme.styles import FOCUS_RING


def mobile_action_dock() -> rx.Component:
    """Feature 48 shell actions; domain mutations are intentionally excluded."""
    return cast(
        rx.Component,
        rx.hstack(
            command_palette_trigger(trigger_id="mobile-command-palette-trigger"),
            rx.button(
                rx.color_mode_cond("Dark theme", "Light theme"),
                on_click=rx.toggle_color_mode,
                aria_label="Toggle light and dark theme",
                style=FOCUS_RING,
                min_height="44px",
            ),
            aria_label="Mobile application actions",
            role="toolbar",
            display=["flex", "flex", "none"],
            position="fixed",
            bottom="max(12px, env(safe-area-inset-bottom))",
            left="50%",
            transform="translateX(-50%)",
            z_index="25",
            padding="8px",
            class_name="bb-glass bb-mobile-action-dock",
        ),
    )
