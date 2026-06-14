from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class BastionEvent(BaseModel):
    event_id: str
    event_type: str
    domain: str | None = None
    topic: str | None = None
    version: int = 1
    created_at: str | None = None
    occurred_at: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    data: dict[str, Any] = Field(default_factory=dict)
    limitations: list[Any] = Field(default_factory=list)
    degraded: bool = False
    stale: bool = False

    model_config = {"extra": "allow"}
