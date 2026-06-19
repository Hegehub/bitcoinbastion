from __future__ import annotations

import reflex as rx

from bastion_ui.components.layout.footer import public_footer
from bastion_ui.components.layout.header import public_header
from bastion_ui.components.layout.public_layout import public_layout
from bastion_ui.components.safety.safety_banner import trace_safety_banner


def public_page(*children: rx.Component) -> rx.Component:
    return public_layout(
        *children,
        header_slot=public_header(),
        footer_slot=public_footer(),
        safety_notice_slot=trace_safety_banner(),
    )
