from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class WebSocketSystemMessage(BaseModel):
    type: Literal["system"] = "system"
    event_type: str
    message: str
    stream: str | None = None
    topics: list[str] = Field(default_factory=list)
    event_types: list[str] | None = None


class WebSocketHeartbeatMessage(BaseModel):
    type: Literal["heartbeat"] = "heartbeat"
    event_type: Literal["heartbeat"] = "heartbeat"
    timestamp: str


class WebSocketErrorMessage(BaseModel):
    type: Literal["error"] = "error"
    event_type: str = "subscription.invalid"
    code: str = "invalid_topic"
    message: str
    recoverable: bool = True
    supported_topics: list[str] = Field(default_factory=list)


class WebSocketEventEnvelope(BaseModel):
    type: Literal["event"] = "event"
    event_id: str
    event_type: str
    domain: str
    topic: str
    version: int
    occurred_at: str
    published_at: str
    data: dict[str, Any] = Field(default_factory=dict)
    limitations: list[Any] = Field(default_factory=list)
    degraded: bool = False
    stale: bool = False
    payload: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
