from __future__ import annotations

from typing import cast

import reflex as rx

from bastion_ui.components.wow._shared import PREVIEW_COPY, wow_card

TILES = ("Trace health", "Evidence health", "Provider health", "Market intelligence", "Policy status", "Audit status", "Deployment/runtime status", "Safety status", "Command shortcuts")


def bastion_command_center() -> rx.Component:
    return cast(rx.Component, rx.grid(*[wow_card(tile, PREVIEW_COPY) for tile in TILES], columns="3", spacing="4", width="100%"))
