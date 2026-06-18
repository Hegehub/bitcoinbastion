from __future__ import annotations

import reflex as rx

from bastion_ui.components.layout.section import section
from bastion_ui.components.public.feature_grid import feature_grid
from bastion_ui.components.public.hero import public_hero
from bastion_ui.components.public.safety_section import SECURITY_WARNING, safety_section
from bastion_ui.components.ui.alert import alert
from bastion_ui.routes._public import public_page

SECURITY_AREAS = (
    (
        "No-custody model",
        "No seed, wallet file, or signing workflow belongs in the UI.",
        "baseline",
    ),
    ("Advisory-only risk model", "Trace and Evidence do not provide legal verdicts.", "baseline"),
    ("Human approval", "Risky actions must remain review-first.", "baseline"),
    (
        "Webhook signatures",
        "Signature behavior must match backend docs before UI claims.",
        "planned",
    ),
    ("API boundaries", "Reflex calls backend APIs and does not copy domain logic.", "baseline"),
    (
        "Sensitive-input rejection",
        "Frontend validators reject obvious wallet-secret material.",
        "baseline",
    ),
    ("Deployment posture", "Operators choose their deployment profile and controls.", "baseline"),
    ("Known limitations", "Provider failures and stale data must remain visible.", "baseline"),
)


def security_page() -> rx.Component:
    return public_page(
        public_hero(
            "Security and no-custody boundaries",
            "Bitcoin Bastion must keep wallet secrets out, expose uncertainty, and preserve "
            "operator approval for risky workflows.",
        ),
        alert(SECURITY_WARNING, "warning"),
        section(feature_grid(SECURITY_AREAS), title="Security posture"),
        safety_section(),
    )
