from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from bastion_ui.domain.provenance import Provenance


class PublicStatusViewModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    platform_status: str
    trace_status: str
    production_calibrated: bool
    modules: tuple[tuple[str, str], ...]
    known_limitations: tuple[str, ...] | None
    last_update: datetime
    provenance: Provenance

    def browser_dump(self) -> dict[str, object]:
        return {
            "platform_status": self.platform_status,
            "trace_status": self.trace_status,
            "production_calibrated": self.production_calibrated,
            "modules": [list(item) for item in self.modules],
            "known_limitations": (
                list(self.known_limitations) if self.known_limitations is not None else None
            ),
            "last_update": self.last_update.isoformat(),
            "provenance": self.provenance.browser_dump(),
        }
