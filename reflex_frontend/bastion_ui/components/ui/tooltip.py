from __future__ import annotations

from typing import cast

import reflex as rx


def tooltip(label: str, content: rx.Component) -> rx.Component:
    return cast(rx.Component, rx.tooltip(content, content=label))
