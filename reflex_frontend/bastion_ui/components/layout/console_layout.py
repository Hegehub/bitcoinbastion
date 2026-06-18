from __future__ import annotations

from typing import cast

import reflex as rx

from bastion_ui.theme.styles import PAGE


def console_layout(
    *children: rx.Component,
    sidebar_slot: rx.Component | None = None,
    topbar_slot: rx.Component | None = None,
    degraded_state_banner_slot: rx.Component | None = None,
    audit_footer_slot: rx.Component | None = None,
) -> rx.Component:
    main_content = rx.vstack(
        *(slot for slot in (topbar_slot, degraded_state_banner_slot) if slot is not None),
        rx.box(*children, width="100%"),
        *(slot for slot in (audit_footer_slot,) if slot is not None),
        width="100%",
        spacing="4",
    )
    return cast(
        rx.Component,
        rx.box(
            rx.hstack(
                *(slot for slot in (sidebar_slot, main_content) if slot is not None),
                align="start",
            ),
            style=PAGE,
        ),
    )
