from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ChildKeyCreatedViewModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    key_id: str
    scopes: tuple[str, ...]
    expires_at: datetime
    warning: str | None
