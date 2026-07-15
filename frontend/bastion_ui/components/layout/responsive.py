from __future__ import annotations

from typing import cast

import reflex as rx

WRAP_LONG_TEXT = {
    "overflow_wrap": "anywhere",
    "word_break": "break-word",
    "max_width": "100%",
}
RESPONSIVE_TABLE_WRAPPER = {
    "width": "100%",
    "overflow_x": "auto",
}


def long_text(value: str) -> rx.Component:
    return cast(rx.Component, rx.text(value, style=WRAP_LONG_TEXT))


def responsive_table_wrapper(*children: rx.Component) -> rx.Component:
    return cast(rx.Component, rx.box(*children, style=RESPONSIVE_TABLE_WRAPPER))
