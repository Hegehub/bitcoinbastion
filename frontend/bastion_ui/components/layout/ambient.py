from __future__ import annotations

from typing import Literal, cast

import reflex as rx


def ambient_geometry(intensity: Literal["low", "normal", "high"] = "normal") -> rx.Component:
    """Presentation-only, pointer-inert geometry; CSS owns bounded motion."""
    return cast(
        rx.Component,
        rx.box(class_name="bb-ambient", aria_hidden="true", data_intensity=intensity),
    )
