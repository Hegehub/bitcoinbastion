from __future__ import annotations

import reflex as rx


def build_bastion_theme() -> rx.Component:
    """Build the canonical Bitcoin Bastion Reflex theme."""

    return rx.theme(
        appearance="dark",
        accent_color="orange",
        radius="large",
    )


__all__ = ["build_bastion_theme"]
