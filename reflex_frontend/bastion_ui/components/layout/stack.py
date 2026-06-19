from __future__ import annotations

from typing import cast

import reflex as rx


def stack(*children: rx.Component) -> rx.Component:
    return cast(rx.Component, rx.vstack(*children, align="start", spacing="4", width="100%"))


def inline_stack(*children: rx.Component) -> rx.Component:
    return cast(rx.Component, rx.hstack(*children, align="center", spacing="3", wrap="wrap"))
