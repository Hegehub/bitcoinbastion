"""Authoritative WebSocket wire contracts owned by the backend."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal, TypeAlias

from pydantic import BaseModel, ConfigDict, Field, JsonValue, TypeAdapter

WIRE_PROTOCOL_FAMILY = "bitcoin-bastion.events"
WIRE_PROTOCOL_VERSION = 1
ACCEPTED_WIRE_VERSIONS = frozenset({WIRE_PROTOCOL_VERSION})


class WireMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    source: str
    advisory_only: bool
    no_custody: Literal[True]
    degraded: bool
    stale: bool
    fallback: bool
    redacted: bool | None = None
    redaction_reason: str | None = None
    unknown_event_type: bool | None = None


class WireEventFrame(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    protocol: Literal["bitcoin-bastion.events"]
    wire_version: Literal[1]
    type: Literal["event"]
    event_id: str
    event_type: str
    domain: str
    topic: str
    version: int = Field(ge=1, description="Deprecated alias of event_version")
    event_version: int = Field(ge=1)
    occurred_at: datetime
    published_at: datetime
    payload: dict[str, JsonValue]
    data: dict[str, JsonValue] = Field(description="Deprecated alias of payload")
    limitations: list[str]
    degraded: bool
    stale: bool
    metadata: WireMetadata


class WireHeartbeatFrame(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    protocol: Literal["bitcoin-bastion.events"]
    wire_version: Literal[1]
    type: Literal["heartbeat"]
    event_type: Literal["heartbeat"]
    timestamp: datetime


class WireSystemFrame(BaseModel):
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


class WireErrorFrame(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    protocol: Literal["bitcoin-bastion.events"]
    wire_version: Literal[1]
    type: Literal["error"]
    event_type: Literal["subscription.invalid", "protocol.unsupported"]
    code: str
    message: str
    recoverable: bool
    supported_topics: list[str]


WireFrame: TypeAlias = Annotated[
    WireEventFrame | WireHeartbeatFrame | WireSystemFrame | WireErrorFrame,
    Field(discriminator="type"),
]
WIRE_FRAME_ADAPTER = TypeAdapter(WireFrame)


def validate_wire_frame_json(frame: str | bytes) -> WireFrame:
    return WIRE_FRAME_ADAPTER.validate_json(frame)
