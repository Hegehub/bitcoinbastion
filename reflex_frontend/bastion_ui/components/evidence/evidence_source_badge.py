from __future__ import annotations

import reflex as rx

from bastion_ui.components.ui.badge import badge


def evidence_source_badge(label: str = "Source not available") -> rx.Component:
    return badge(label, "info")
