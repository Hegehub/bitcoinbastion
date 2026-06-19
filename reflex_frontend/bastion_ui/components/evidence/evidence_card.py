from __future__ import annotations

from typing import Any

import reflex as rx

from bastion_ui.components.evidence.evidence_confidence_badge import evidence_confidence_badge
from bastion_ui.components.evidence.evidence_source_badge import evidence_source_badge
from bastion_ui.components.ui.card import card


def _value(item: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = item.get(key)
        if value not in (None, ""):
            return str(value)
    return "Not available"


def evidence_card(item: dict[str, Any] | None = None) -> rx.Component:
    payload = item or {}
    return card(
        rx.hstack(
            evidence_source_badge(_value(payload, "source_name", "source", "provider")),
            evidence_confidence_badge(_value(payload, "confidence", "quality", "freshness")),
            wrap="wrap",
        ),
        rx.text("Type: " + _value(payload, "type", "evidence_type", "category")),
        rx.text("Timestamp: " + _value(payload, "timestamp", "generated_at", "observed_at")),
        rx.text("Provider status: " + _value(payload, "provider_status", "status")),
        rx.text("Limitations: " + _value(payload, "limitations", "limitation")),
        title=_value(payload, "title", "name", "id"),
        subtitle="Provider did not return missing fields; no values are invented.",
        variant="evidence",
    )
