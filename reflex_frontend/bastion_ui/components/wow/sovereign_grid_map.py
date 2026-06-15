from __future__ import annotations

import reflex as rx

from bastion_ui.components.wow._shared import wow_card

NODES = ("FastAPI API", "Worker", "Beat", "PostgreSQL", "Redis", "Provider sources", "Evidence storage", "Runtime profile", "External integrations")


def sovereign_grid_map() -> rx.Component:
    return wow_card("Sovereign Grid Map", *[f"{node}: unknown/missing state visible" for node in NODES])
