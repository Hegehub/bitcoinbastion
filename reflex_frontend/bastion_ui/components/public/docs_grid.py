from __future__ import annotations

import reflex as rx

from bastion_ui.components.layout.grid import responsive_grid
from bastion_ui.components.public.pillar_card import pillar_card

DOC_CARDS: tuple[tuple[str, str, str], ...] = (
    ("Platform", "Architecture and product surface overview.", "baseline"),
    ("Trace", "Public Trace flow documentation is pending Prompt 7.", "planned"),
    ("Evidence", "Evidence concepts and limitations.", "baseline"),
    ("Developer API", "Public API contract and client foundation.", "baseline"),
    ("Webhooks", "Webhook documentation depends on backend contract confirmation.", "pending"),
    ("WebSocket", "Realtime documentation depends on backend contract confirmation.", "pending"),
    ("SDK", "SDK references are previews unless package status is confirmed.", "planned"),
    ("Runtime Profiles", "Deployment profiles and operator modes.", "baseline"),
    ("Deployment", "Docker, Kubernetes, and local deployment guidance.", "baseline"),
    ("Security", "No-custody and sensitive-input boundaries.", "baseline"),
    ("Roadmap", "Migration plan and parity gates.", "baseline"),
    ("Production Readiness", "Readiness notes remain conservative.", "pending"),
)


def docs_grid() -> rx.Component:
    return responsive_grid(
        *[pillar_card(title, body, status=status) for title, body, status in DOC_CARDS]
    )
