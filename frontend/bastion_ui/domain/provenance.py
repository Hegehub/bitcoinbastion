from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, model_validator


class ProvenanceState(StrEnum):
    LIVE = "LIVE"
    VERIFIED_SNAPSHOT = "VERIFIED_SNAPSHOT"
    DEMO_FIXTURE = "DEMO_FIXTURE"
    UNAVAILABLE = "UNAVAILABLE"


class Provenance(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    state: ProvenanceState
    source_label: str
    observed_at: datetime | None = None
    captured_at: datetime | None = None
    source_revision: str | None = None
    integrity_reference: str | None = None
    limitation: str | None = None
    unavailable_reason: str | None = None

    @model_validator(mode="after")
    def validate_authority(self) -> Provenance:
        if self.state is ProvenanceState.VERIFIED_SNAPSHOT and not all(
            (self.captured_at, self.source_revision, self.integrity_reference)
        ):
            raise ValueError("verified_snapshot_authority_required")
        if self.state is ProvenanceState.UNAVAILABLE and not self.unavailable_reason:
            raise ValueError("unavailable_reason_required")
        return self

    def browser_dump(self) -> dict[str, str | None]:
        """Explicit allowlist for browser State; no raw payload can pass through."""
        return {
            "state": self.state.value,
            "source_label": self.source_label,
            "observed_at": self.observed_at.isoformat() if self.observed_at else None,
            "captured_at": self.captured_at.isoformat() if self.captured_at else None,
            "source_revision": self.source_revision,
            "integrity_reference": self.integrity_reference,
            "limitation": self.limitation,
            "unavailable_reason": self.unavailable_reason,
        }
