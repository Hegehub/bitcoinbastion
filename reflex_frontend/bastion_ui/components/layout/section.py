from __future__ import annotations

from typing import cast

import reflex as rx

from bastion_ui.theme.styles import SECTION


def section(*children: rx.Component, title: str | None = None) -> rx.Component:
    heading = rx.heading(title, size="5") if title else rx.fragment()
    return cast(rx.Component, rx.section(heading, *children, style=SECTION))
