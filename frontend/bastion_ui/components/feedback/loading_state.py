from __future__ import annotations

from typing import cast

import reflex as rx

from bastion_ui.components.ui.skeleton import skeleton


def loading_state(label: str = "Loading advisory view") -> rx.Component:
    return cast(rx.Component, rx.vstack(rx.text(label), skeleton("card"), width="100%"))
