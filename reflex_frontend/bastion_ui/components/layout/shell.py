from __future__ import annotations

import reflex as rx

from bastion_ui.components.layout.console_layout import console_layout
from bastion_ui.components.layout.public_layout import public_layout


def page_shell(title: str, *children: rx.Component) -> rx.Component:
    return public_layout(rx.heading(title, size="6"), *children)


def public_shell(*children: rx.Component) -> rx.Component:
    return public_layout(*children)


def console_shell(*children: rx.Component) -> rx.Component:
    return console_layout(*children)
