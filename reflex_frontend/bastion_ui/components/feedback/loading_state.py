from __future__ import annotations

from typing import cast

import reflex as rx

from bastion_ui.components.ui.skeleton import skeleton


def loading_state(message: str = "Loading data.") -> rx.Component:
    return cast(rx.Component, rx.vstack(skeleton("line"), rx.text(message, color="gray")))
