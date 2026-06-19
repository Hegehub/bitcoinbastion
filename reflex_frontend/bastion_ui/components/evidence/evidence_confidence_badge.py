from __future__ import annotations

import reflex as rx

from bastion_ui.components.ui.badge import badge


def evidence_confidence_badge(label: str = "Confidence unavailable") -> rx.Component:
    normalized = label.lower()
    if "low" in normalized or "limited" in normalized:
        return badge(label, "warning")
    if "high" in normalized or "strong" in normalized:
        return badge(label, "success")
    return badge(label, "neutral")
