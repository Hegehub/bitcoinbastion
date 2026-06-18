from __future__ import annotations

from typing import cast

import reflex as rx


def stack(*children: rx.Component, spacing: str = "4") -> rx.Component:
    return cast(rx.Component, rx.vstack(*children, align="start", spacing=spacing, width="100%"))


def inline_stack(*children: rx.Component, spacing: str = "3") -> rx.Component:
    return cast(rx.Component, rx.hstack(*children, align="center", spacing=spacing, wrap="wrap"))
