from __future__ import annotations

from typing import cast

import reflex as rx


def divider() -> rx.Component:
    return cast(rx.Component, rx.divider(width="100%"))
