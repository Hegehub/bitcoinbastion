from __future__ import annotations

from typing import cast

import reflex as rx


def text_input(placeholder: str, name: str) -> rx.Component:
    return cast(rx.Component, rx.input(placeholder=placeholder, name=name, width="100%"))
