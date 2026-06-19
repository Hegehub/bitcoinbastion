from __future__ import annotations

import reflex as rx

from bastion_ui.components.ui.alert import alert

NO_CUSTODY_COPY = "No custody. Public Bitcoin addresses only. Never enter seed phrases, private keys, wallet files or signing material."  # noqa: E501


def no_custody_notice() -> rx.Component:
    return alert(NO_CUSTODY_COPY, "warning")
