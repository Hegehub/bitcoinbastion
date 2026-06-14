from __future__ import annotations

from typing import Literal, cast

import reflex as rx

from bastion_ui.theme.tokens import BASTION_DANGER, BASTION_GRAPHITE, BITCOIN_ORANGE

ButtonVariant = Literal["primary", "secondary", "danger", "ghost"]


def button(label: str, href: str | None = None, variant: ButtonVariant = "primary") -> rx.Component:
    styles = {
        "primary": {"background": BITCOIN_ORANGE, "color": "#111111"},
        "secondary": {"background": "white", "color": BASTION_GRAPHITE},
        "danger": {"background": BASTION_DANGER, "color": "white"},
        "ghost": {"background": "transparent", "color": BASTION_GRAPHITE},
    }[variant]
    component = rx.button(label, **styles, border_radius="999px", padding="0.75rem 1rem")
    if href is None:
        return cast(rx.Component, component)
    return cast(rx.Component, rx.link(component, href=href))
