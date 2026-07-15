from __future__ import annotations

import reflex as rx


class PreferencesState(rx.State):
    reduced_motion: bool = True

    def set_reduced_motion(self, value: bool) -> None:
        self.reduced_motion = value

    def toggle_reduced_motion(self) -> None:
        self.reduced_motion = not self.reduced_motion
