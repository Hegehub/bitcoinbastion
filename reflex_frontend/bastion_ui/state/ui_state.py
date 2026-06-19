from __future__ import annotations

import reflex as rx


class UIState(rx.State):
    reduced_motion: bool = False
    command_palette_open: bool = False

    def set_reduced_motion(self, value: bool) -> None:
        self.reduced_motion = value

    def set_command_palette_open(self, value: bool) -> None:
        self.command_palette_open = value

    def toggle_command_palette(self) -> None:
        self.command_palette_open = not self.command_palette_open
