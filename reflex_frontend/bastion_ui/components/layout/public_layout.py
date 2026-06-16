from __future__ import annotations

from typing import cast

import reflex as rx

from bastion_ui.components.layout.container import container
from bastion_ui.theme.styles import PAGE


def public_layout(
    *children: rx.Component,
    header_slot: rx.Component | None = None,
    footer_slot: rx.Component | None = None,
    safety_notice_slot: rx.Component | None = None,
) -> rx.Component:
    content = []
    if header_slot is not None:
        content.append(header_slot)
    if safety_notice_slot is not None:
        content.append(safety_notice_slot)
    content.append(rx.box(container(*children), id="main-content"))
    if footer_slot is not None:
        content.append(footer_slot)
    return cast(rx.Component, rx.box(*content, style=PAGE))
