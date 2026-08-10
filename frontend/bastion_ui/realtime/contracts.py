from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, JsonValue, TypeAdapter

WIRE_PROTOCOL = "bitcoin-bastion.events"
WIRE_VERSION = 1


class SystemFrame(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    protocol: Literal["bitcoin-bastion.events"]
    wire_version: Literal[1]
    type: Literal["system"]
    event_type: Literal["connection.accepted", "replay.not_available"]
    message: str
    stream: str | None = None
    topics: list[str] | None = None
    event_types: list[str] | None = None
    last_event_id: str | None = None


class HeartbeatFrame(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    protocol: Literal["bitcoin-bastion.events"]
    wire_version: Literal[1]
    type: Literal["heartbeat"]
    event_type: Literal["heartbeat"]
    timestamp: datetime


class EventFrame(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    protocol: Literal["bitcoin-bastion.events"]
    wire_version: Literal[1]
    type: Literal["event"]
    event_id: str
    event_type: str
    domain: str
    topic: str
    version: int = Field(ge=1)
    event_version: int = Field(ge=1)
    occurred_at: datetime
    published_at: datetime
    payload: dict[str, JsonValue]
    data: dict[str, JsonValue]
    limitations: list[str]
    degraded: bool
    stale: bool
    metadata: dict[str, JsonValue]


class ErrorFrame(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    protocol: Literal["bitcoin-bastion.events"]
    wire_version: Literal[1]
    type: Literal["error"]
    event_type: Literal["subscription.invalid", "protocol.unsupported"]
    code: str
    message: str
    recoverable: bool
    supported_topics: list[str]


type Frame = Annotated[
    SystemFrame | HeartbeatFrame | EventFrame | ErrorFrame, Field(discriminator="type")
]
FRAME_ADAPTER: TypeAdapter[Frame] = TypeAdapter(Frame)


def decode_frame(raw: str | bytes) -> Frame:
    return FRAME_ADAPTER.validate_json(raw)
