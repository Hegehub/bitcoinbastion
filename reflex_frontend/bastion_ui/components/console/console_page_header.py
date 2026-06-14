from __future__ import annotations

from typing import cast

import reflex as rx

from bastion_ui.components.console.operator_notice import operator_notice
from bastion_ui.components.console.readonly_badge import readonly_badge_group


def console_page_header(title: str, description: str) -> rx.Component:
    return cast(rx.Component, rx.vstack(rx.heading(title, size="7"), rx.text(description), readonly_badge_group(), operator_notice(), align="start", spacing="3", width="100%"))
