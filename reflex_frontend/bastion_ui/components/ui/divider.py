from __future__ import annotations

from typing import cast

import reflex as rx

from bastion_ui.theme.tokens import BASTION_BORDER


def divider() -> rx.Component:
    return cast(rx.Component, rx.box(height="1px", width="100%", background=BASTION_BORDER))
