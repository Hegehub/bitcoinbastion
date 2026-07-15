from __future__ import annotations

import reflex as rx

from bastion_ui.components.ui.badge import badge
from bastion_ui.security.safety_copy import STALE_DATA


def stale_data_badge(label: str = STALE_DATA) -> rx.Component:
    return badge(label, "warning")
