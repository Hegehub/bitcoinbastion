from __future__ import annotations

from typing import cast

import reflex as rx

from bastion_ui.theme.styles import CARD


def table(headers: list[str], rows: list[list[str]]) -> rx.Component:
    header_row = rx.table.row(*[rx.table.column_header_cell(header) for header in headers])
    body_rows = [rx.table.row(*[rx.table.cell(cell) for cell in row]) for row in rows]
    return cast(
        rx.Component,
        rx.box(rx.table.root(rx.table.header(header_row), rx.table.body(*body_rows)), style=CARD),
    )
