from __future__ import annotations

import reflex as rx

from bastion_ui.components.layout.grid import responsive_grid
from bastion_ui.components.public.pillar_card import pillar_card


def runtime_profile_preview() -> rx.Component:
    profiles = (
        ("Docker Compose", "Local and small-team orchestration baseline.", "baseline"),
        ("Kubernetes", "Cluster deployment path requiring operator validation.", "planned"),
        ("k3s", "Lightweight cluster path for sovereignty-first operators.", "planned"),
        ("kind", "Local Kubernetes test profile.", "experimental"),
        ("minikube", "Local Kubernetes development profile.", "experimental"),
        ("single-node", "Single-machine deployment path.", "baseline"),
        ("bare-metal/systemd", "Direct host operation with explicit operator control.", "planned"),
    )
    return responsive_grid(*[pillar_card(title, body, label) for title, body, label in profiles])
