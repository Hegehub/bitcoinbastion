from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from bastion_ui.domain.provenance import Provenance


class StreamStatusViewModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    stream: str
    message: str
    topics: tuple[str, ...]
    wire_version: int
    provenance: Provenance

    def browser_dump(self) -> dict[str, object]:
        return {
            "stream": self.stream,
            "message": self.message,
            "topics": list(self.topics),
            "wire_version": self.wire_version,
            "provenance": self.provenance.browser_dump(),
        }
