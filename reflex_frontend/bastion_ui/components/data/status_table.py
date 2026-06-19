from __future__ import annotations

from typing import Any

import reflex as rx

from bastion_ui.components.ui.table import table


def status_table(rows: list[dict[str, Any]] | None = None) -> rx.Component:
    if not rows:
        return table(
            ["System", "State", "Note"],
            [["Provider A", "Degraded", "Manual review recommended"]],
        )
    headers = list(rows[0].keys())
    values = [[str(row.get(header, "")) for header in headers] for row in rows]
    return table(headers, values)
