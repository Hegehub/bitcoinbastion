from __future__ import annotations

import reflex as rx

from bastion_ui.components.ui.alert import alert

ADVISORY_COPY = "Advisory-only. Not legal verification. Not Bitcoin consensus proof."


def advisory_notice() -> rx.Component:
    return alert(ADVISORY_COPY, "advisory")


def market_intelligence_notice() -> rx.Component:
    return alert("Market intelligence is informational and not financial advice.", "advisory")


def treasury_review_notice() -> rx.Component:
    return alert(
        "Treasury workflows require review and approval. This interface does not custody funds or sign transactions.",  # noqa: E501
        "advisory",
    )
