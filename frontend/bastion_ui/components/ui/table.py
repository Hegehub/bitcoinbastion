from __future__ import annotations

from typing import cast

import reflex as rx


def table(headers: list[str], rows: list[list[str]]) -> rx.Component:
    return cast(
        rx.Component,
        rx.box(
            rx.table.root(
                rx.table.header(rx.table.row(*[rx.table.column_header_cell(h) for h in headers])),
                rx.table.body(
                    *[
                        rx.table.row(
                            *[
                                rx.table.cell(cell, data_label=headers[index])
                                for index, cell in enumerate(row)
                            ]
                        )
                        for row in rows
                    ]
                ),
                width="100%",
            ),
            class_name="bb-responsive-table",
            overflow_x="auto",
            width="100%",
        ),
    )
