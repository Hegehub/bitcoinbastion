from __future__ import annotations

from typing import cast

import reflex as rx


def key_value(label: str, value: str) -> rx.Component:
    return cast(rx.Component, rx.hstack(rx.text(label, weight="bold"), rx.text(value)))
