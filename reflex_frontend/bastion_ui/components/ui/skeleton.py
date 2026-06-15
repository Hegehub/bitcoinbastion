from __future__ import annotations

from typing import cast

import reflex as rx


def skeleton(width: str = "100%", height: str = "1rem") -> rx.Component:
    return cast(rx.Component, rx.box(width=width, height=height, background="#E5E7EB", border_radius="8px"))
