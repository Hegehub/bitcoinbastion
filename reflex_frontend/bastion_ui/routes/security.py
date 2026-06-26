from __future__ import annotations

import reflex as rx

from bastion_ui.components.public.feature_grid import feature_grid
from bastion_ui.components.public.safety_section import SECURITY_WARNING
from bastion_ui.components.ui.alert import alert
from bastion_ui.routes._shared import public_page


def security_page() -> rx.Component:
    topics = (
        (
            "No-custody model",
            "Bitcoin Bastion does not custody funds or sign transactions.",
            "implemented",
        ),
        (
            "No wallet-secret input",
            "Frontend validation must reject wallet-secret-like material.",
            "baseline",
        ),
        ("Advisory risk model", "Risk and evidence signals require human review.", "implemented"),
        ("Human approval", "Risky actions must not execute automatically.", "baseline"),
        (
            "Webhook signatures",
            "Webhook security must be verified before docs claim completeness.",
            "experimental",
        ),
        (
            "API boundaries",
            "Reflex calls backend APIs and does not duplicate backend domain logic.",
            "baseline",
        ),
        (
            "Deployment posture",
            "Self-hosted deployments require operator security review.",
            "baseline",
        ),
        (
            "Known limitations",
            "Provider disagreement, stale data, and degraded states must remain visible.",
            "baseline",
        ),
    )
    return public_page(
        "Security",
        alert(SECURITY_WARNING, "warning"),
        feature_grid(topics),
        subtitle="No-custody safety boundaries and known limitations.",
    )
