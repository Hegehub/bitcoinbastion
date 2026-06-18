from __future__ import annotations

import reflex as rx

from bastion_ui.navigation import CommandAction, search_command_actions


class CommandPaletteState(rx.State):
    open: bool = False
    query: str = ""

    def set_open(self, value: bool) -> None:
        self.open = value

    def toggle(self) -> None:
        self.open = not self.open

    def set_query(self, value: str) -> None:
        self.query = value

    @rx.var
    def filtered_actions(self) -> list[CommandAction]:
        return list(search_command_actions(self.query))
