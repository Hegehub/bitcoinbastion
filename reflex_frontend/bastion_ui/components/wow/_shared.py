from __future__ import annotations

from typing import Any

import reflex as rx

from bastion_ui.components.ui.card import card, safety_card

REQUIRED_WOW_SAFETY = (
    "Advisory-only.",
    "Not legal verification.",
    "Not Bitcoin consensus proof.",
    "No custody.",
    "Public Bitcoin addresses only.",
    "Never enter seed phrases, private keys, wallet files or signing material.",
    "Historical similarity does not guarantee future market behavior.",
    "Correlation is not proof of causation.",
    "Operator review required for risky actions.",
)

PREVIEW_COPY = "Preview only. Backend remains the source of truth. Degraded, fallback, stale, and unavailable states remain visible."


def wow_card(title: str, *lines: str) -> rx.Component:
    body = lines or (PREVIEW_COPY,)
    return card(*[rx.text(line) for line in body], title=title)


def wow_safety_card(title: str = "No-Custody Safety Layer") -> rx.Component:
    return safety_card(*[rx.text(line) for line in REQUIRED_WOW_SAFETY], title=title)


def summarize(data: dict[str, Any] | None, key: str, fallback: str = "unknown") -> str:
    if not data:
        return fallback
    value = data.get(key, fallback)
    return str(value) if value is not None else fallback
