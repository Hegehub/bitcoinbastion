from __future__ import annotations

import reflex as rx

from bastion_ui.components.layout.app_shell import app_shell
from bastion_ui.components.layout.container import container


def public_layout(
    *children: rx.Component,
    header: rx.Component | None = None,
    footer: rx.Component | None = None,
    safety_notice: rx.Component | None = None,
) -> rx.Component:
    return app_shell(
        container(safety_notice or rx.fragment(), *children),
        header=header,
        footer=footer,
    )
