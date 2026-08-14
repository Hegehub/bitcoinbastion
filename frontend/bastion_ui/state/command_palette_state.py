from __future__ import annotations

import reflex as rx
from reflex.event import EventSpec

from bastion_ui.command_registry import command_destination, search_commands


def _results(query: str) -> list[dict[str, str]]:
    return [
        {
            "id": command.id,
            "label": command.label,
            "route_id": command.route_id or "",
            "domain": command.domain,
            "type": command.type.value,
        }
        for command in search_commands(query)
    ]


class CommandPaletteState(rx.State):
    """Presentation-only palette state; it owns no domain or security data."""

    open: bool = False
    query: str = ""
    selected_index: int = 0
    results: list[dict[str, str]] = _results("")
    focus_return_id: str = "command-palette-trigger"

    def open_palette(self, focus_return_id: str = "command-palette-trigger") -> None:
        self.open = True
        self.focus_return_id = focus_return_id
        self.query = ""
        self.selected_index = 0
        self.results = _results("")

    def close_palette(self) -> EventSpec:
        self.open = False
        self.query = ""
        return rx.set_focus(self.focus_return_id)

    def toggle_open(self) -> EventSpec | None:
        if self.open:
            return self.close_palette()
        self.open_palette()
        return None

    def set_query(self, value: str) -> None:
        self.query = value
        self.selected_index = 0
        self.results = _results(value)

    def select_next(self) -> None:
        if self.results:
            self.selected_index = (self.selected_index + 1) % len(self.results)

    def select_previous(self) -> None:
        if self.results:
            self.selected_index = (self.selected_index - 1) % len(self.results)

    def handle_key(self, key: str) -> EventSpec | None:
        if key == "Escape":
            return self.close_palette()
        if key == "ArrowDown":
            self.select_next()
        elif key == "ArrowUp":
            self.select_previous()
        elif key == "Enter" and self.results:
            return self.activate(self.results[self.selected_index]["route_id"])
        return None

    def activate(self, route_id: str) -> EventSpec:
        command = next(
            (command for command in search_commands("") if command.route_id == route_id), None
        )
        if command is None:
            raise ValueError("command route is disabled, denied, or unknown")
        self.open = False
        self.query = ""
        return rx.redirect(command_destination(command))
