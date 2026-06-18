from __future__ import annotations

from typing import cast

import reflex as rx


def advisory_notice() -> rx.Component:
    return cast(
        rx.Component,
        rx.vstack(
            rx.text("Advisory-only.", weight="bold"),
            rx.text("Not legal verification."),
            rx.text("Not Bitcoin consensus proof."),
            align="start",
        ),
    )


def market_intelligence_notice() -> rx.Component:
    return cast(
        rx.Component,
        rx.text("Market intelligence is informational and not financial advice."),
    )


def treasury_review_notice() -> rx.Component:
    return cast(
        rx.Component,
        rx.text(
            "Treasury workflows require review and approval. This interface does not custody "
            "funds or sign transactions."
        ),
    )
