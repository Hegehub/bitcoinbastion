from __future__ import annotations

import reflex as rx

from bastion_ui.components.wow._shared import wow_card


def node_pulse() -> rx.Component:
    return wow_card("Node Pulse", "latest known block height: unknown", "provider confidence: unknown", "stale/fallback warning: visible", "mempool/fee pressure: unavailable placeholder", "No custody. Node sync is not implied without backend data.")
