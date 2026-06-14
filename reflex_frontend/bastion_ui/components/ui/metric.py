from __future__ import annotations

from typing import cast

import reflex as rx

from bastion_ui.theme.styles import CARD


def metric(label: str, value: str, helper: str = "") -> rx.Component:
    return cast(rx.Component, rx.box(rx.text(label), rx.heading(value, size="6"), rx.text(helper), style=CARD))
