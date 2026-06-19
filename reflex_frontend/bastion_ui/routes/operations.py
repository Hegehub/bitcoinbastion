from __future__ import annotations

import reflex as rx

from bastion_ui.components.layout.section import section
from bastion_ui.components.public.hero import public_hero
from bastion_ui.components.public.runtime_profile_preview import runtime_profile_preview
from bastion_ui.components.public.safety_section import safety_section
from bastion_ui.components.ui.card import card
from bastion_ui.routes._public import public_page


def operations_page() -> rx.Component:
    return public_page(
        public_hero(
            "Self-hosted operations without cloud lock-in",
            "Bitcoin Bastion favors local-first deployment, operator review, evidence-driven "
            "posture, and transparent fallback states.",
            primary_label="View runtime profiles",
            primary_href="/operations",
            secondary_label="Security posture",
            secondary_href="/security",
        ),
        section(
            runtime_profile_preview(),
            card(
                rx.text("Docker Compose is the baseline local path."),
                rx.text("Kubernetes, k3s, kind, minikube, and systemd paths are not equivalent."),
                title="Deployment philosophy",
            ),
            title="Runtime profile matrix preview",
        ),
        safety_section(),
    )
