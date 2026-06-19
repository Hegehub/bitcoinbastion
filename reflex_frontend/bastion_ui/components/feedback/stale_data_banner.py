from __future__ import annotations

import reflex as rx

from bastion_ui.components.ui.alert import alert


def stale_data_banner() -> rx.Component:
    return alert("Stale data. This view may be incomplete. Manual review recommended.", "stale")
