from __future__ import annotations

import reflex as rx

from bastion_ui.components.public.feature_grid import feature_grid
from bastion_ui.routes._shared import public_page


def manifesto_page() -> rx.Component:
    principles = (
        (
            "Bitcoin-first",
            "Bitcoin systems deserve infrastructure that respects sovereignty.",
            "baseline",
        ),
        (
            "No custody",
            "Bitcoin Bastion must not hold funds or request wallet secrets.",
            "implemented",
        ),
        (
            "Evidence over claims",
            "Source material and limitations matter more than verdict language.",
            "baseline",
        ),
        (
            "Operator control",
            "Risky actions require human approval and rollback discipline.",
            "baseline",
        ),
        (
            "Self-hostability",
            "Operators should be able to run locally and avoid cloud lock-in.",
            "baseline",
        ),
        (
            "Explicit limitations",
            "Advisory intelligence is not legal verification or consensus proof.",
            "implemented",
        ),
        (
            "No black-box trust",
            "Systems should expose data source quality and degraded states.",
            "baseline",
        ),
        ("Auditability", "Review trails and evidence context should be preserved.", "planned"),
    )
    return public_page(
        "Manifesto",
        feature_grid(principles),
        subtitle="Strong principles, conservative claims, and human approval for risky actions.",
    )
