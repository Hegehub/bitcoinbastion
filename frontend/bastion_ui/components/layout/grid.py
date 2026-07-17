from __future__ import annotations

from typing import cast

import reflex as rx

from bastion_ui.theme.responsive import RESPONSIVE_GRID_COLUMNS


def responsive_grid(*children: rx.Component) -> rx.Component:
    return cast(
        rx.Component,
        rx.grid(*children, grid_template_columns=RESPONSIVE_GRID_COLUMNS, gap="16px", width="100%"),
    )


def two_column_grid(*children: rx.Component) -> rx.Component:
    return cast(
        rx.Component,
        rx.grid(
            *children, grid_template_columns="repeat(2, minmax(0, 1fr))", gap="16px", width="100%"
        ),
    )


def three_column_grid(*children: rx.Component) -> rx.Component:
    return cast(
        rx.Component,
        rx.grid(
            *children, grid_template_columns="repeat(3, minmax(0, 1fr))", gap="16px", width="100%"
        ),
    )
