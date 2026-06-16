from __future__ import annotations

from typing import cast

import reflex as rx


def tooltip(label: str, content: str) -> rx.Component:
    return cast(rx.Component, rx.tooltip(rx.text(label), content=content))
