from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class IntelligenceHealthViewModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    status: str
    degraded: bool
    provider_confidence: Decimal
    last_success: datetime | None
    last_failure: datetime | None
    limitations: tuple[str, ...] | None
