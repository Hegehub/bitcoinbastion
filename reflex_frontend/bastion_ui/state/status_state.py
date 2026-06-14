from __future__ import annotations

import reflex as rx


class StatusState(rx.State):
    status_message: str = "Status is advisory and pending production evidence."
