from __future__ import annotations

from typing import cast

import reflex as rx

from bastion_ui.theme.styles import CONTAINER


def container(*children: rx.Component) -> rx.Component:
    return cast(rx.Component, rx.box(*children, style=CONTAINER))
