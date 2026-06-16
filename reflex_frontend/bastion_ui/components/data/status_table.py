from __future__ import annotations

import reflex as rx

from bastion_ui.components.ui.table import table


def status_table() -> rx.Component:
    return table(
        ["System", "State", "Note"],
        [["Provider A", "Degraded", "Manual review recommended"]],
    )
