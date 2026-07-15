from __future__ import annotations

from typing import Any

import reflex as rx

from bastion_ui.components.evidence.evidence_confidence_badge import evidence_confidence_badge
from bastion_ui.components.evidence.evidence_source_badge import evidence_source_badge
from bastion_ui.components.ui.card import card


def _field(item: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = item.get(key)
        if value not in (None, ""):
            return str(value)
    return "Not available"


def evidence_card(item: dict[str, Any] | None = None) -> rx.Component:
    data = item or {}
    return card(
        rx.hstack(
            evidence_source_badge(_field(data, "source", "source_name", "provider")),
            evidence_confidence_badge(_field(data, "confidence", "quality", "score")),
            wrap="wrap",
        ),
        rx.text("Type: ", _field(data, "type", "evidence_type", "title")),
        rx.text("Category: ", _field(data, "category", "source_category")),
        rx.text("Timestamp: ", _field(data, "timestamp", "generated_at", "observed_at")),
        rx.text("Freshness: ", _field(data, "freshness", "stale")),
        rx.text("Limitations: ", _field(data, "limitations", "limitation")),
        rx.text("Provider status: ", _field(data, "provider_status", "status")),
        title=_field(data, "title", "name", "evidence_type"),
        variant="evidence",
    )
