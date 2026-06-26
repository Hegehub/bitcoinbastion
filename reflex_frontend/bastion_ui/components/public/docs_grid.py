from __future__ import annotations

import reflex as rx

from bastion_ui.components.layout.grid import responsive_grid
from bastion_ui.components.public.pillar_card import pillar_card

DOC_CARDS = (
    ("Platform", "Overview of the platform architecture.", "baseline"),
    ("Trace", "Trace workflow documentation is pending route migration.", "planned"),
    ("Evidence", "Evidence and Proof Packet concepts.", "baseline"),
    ("Developer API", "Public API and client contract references.", "baseline"),
    ("Webhooks", "Webhook docs are pending validation.", "pending"),
    ("WebSocket", "Realtime interface docs are pending validation.", "pending"),
    ("SDK", "SDK docs are planned when the SDK contract is stable.", "planned"),
    ("Runtime Profiles", "Deployment profile documentation.", "baseline"),
    ("Deployment", "Docker, Kubernetes, k3s, kind, and bare-metal notes.", "baseline"),
    ("Security", "No-custody and frontend safety boundaries.", "baseline"),
    ("Roadmap", "Migration sequence and blockers.", "baseline"),
    ("Production Readiness", "Readiness evidence remains conservative.", "pending"),
)


def docs_grid() -> rx.Component:
    return responsive_grid(*[pillar_card(title, body, label) for title, body, label in DOC_CARDS])
