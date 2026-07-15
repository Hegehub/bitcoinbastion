from __future__ import annotations

import reflex as rx

from bastion_ui.components.ui.badge import badge


def evidence_confidence_badge(confidence: str = "Confidence not available") -> rx.Component:
    return badge(confidence or "Confidence not available", "warning")
