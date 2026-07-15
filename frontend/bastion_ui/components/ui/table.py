from __future__ import annotations

from typing import cast

import reflex as rx


def table(headers: list[str], rows: list[list[str]]) -> rx.Component:
    return cast(
        rx.Component,
        rx.table.root(
            rx.table.header(rx.table.row(*[rx.table.column_header_cell(h) for h in headers])),
            rx.table.body(*[rx.table.row(*[rx.table.cell(c) for c in row]) for row in rows]),
            width="100%",
        ),
    )
