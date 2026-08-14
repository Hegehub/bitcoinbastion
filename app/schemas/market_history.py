"""Strict browser-safe contracts for historical Market intelligence."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Annotated, Literal
from uuid import UUID

from pydantic import AnyUrl, BaseModel, ConfigDict, Field, StringConstraints, field_validator

SafeText = Annotated[str, StringConstraints(max_length=2000)]


class StrictHistoryModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class TimelineKind(StrEnum):
    NEWS = "NEWS"
    SIGNAL = "SIGNAL"
    MARKET = "MARKET"
    NARRATIVE = "NARRATIVE"
    PROVIDER = "PROVIDER"
    OTHER = "OTHER"


class MarketSourceType(StrEnum):
    INTERNAL = "INTERNAL"
    NEWS = "NEWS"
    SIGNAL = "SIGNAL"
    PROVIDER = "PROVIDER"
    MARKET_DATA = "MARKET_DATA"
    UNKNOWN = "UNKNOWN"


class MarketSourceRef(StrictHistoryModel):
    source_id: str
    display_name: str
    source_type: MarketSourceType


class MarketEvidenceRelation(StrEnum):
    RELATED_EVIDENCE = "RELATED_EVIDENCE"
    SOURCE_MATERIAL = "SOURCE_MATERIAL"


class MarketEvidenceLink(StrictHistoryModel):
    evidence_id: int
    relation: MarketEvidenceRelation
    label: str
    linked_at: datetime
    verification_status: Literal["NOT_REQUESTED", "INTEGRITY_RECORD_AVAILABLE"]


class MarketTimelineEventOut(StrictHistoryModel):
    event_id: int
    sequence: int
    kind: TimelineKind
    producer_type: str
    occurred_at: datetime
    observed_at: datetime
    source: MarketSourceRef
    title: str
    summary: SafeText
    related_signal_id: int | None = None
    related_candle_id: int | None = None
    evidence_links: tuple[MarketEvidenceLink, ...] = ()
    limitations: tuple[str, ...] = ()


class MarketTimelinePageOut(StrictHistoryModel):
    items: tuple[MarketTimelineEventOut, ...]
    limit: int
    next_before_sequence: int | None = None
    ordering: Literal["occurred_at_desc,event_id_desc"] = "occurred_at_desc,event_id_desc"


class ReplayIntegrityOut(StrictHistoryModel):
    algorithm: Literal["sha256"] = "sha256"
    content_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    meaning: Literal["CONTENT_EQUALITY_ONLY"] = "CONTENT_EQUALITY_ONLY"


class MarketReplayCaptureOut(StrictHistoryModel):
    capture_id: UUID
    schema_version: Literal["market-replay.capture.v1"] = "market-replay.capture.v1"
    captured_at: datetime
    effective_at: datetime
    event: MarketTimelineEventOut
    integrity: ReplayIntegrityOut
    historical: Literal[True] = True
    limitations: tuple[str, ...] = ()


class AttributionRelation(StrEnum):
    ASSOCIATED = "ASSOCIATED"
    CORRELATION_CANDIDATE = "CORRELATION_CANDIDATE"


class MarketAttributionOut(StrictHistoryModel):
    attribution_id: int
    subject_candle_id: int
    factor_event_id: int | None
    relation: AttributionRelation
    confidence_ratio: float = Field(ge=0, le=1)
    explanation: SafeText
    limitations: tuple[str, ...]
    evidence_links: tuple[MarketEvidenceLink, ...] = ()


class NarrativeOrigin(StrEnum):
    STORED_BACKEND_RECORD = "STORED_BACKEND_RECORD"


class MarketNarrativeOut(StrictHistoryModel):
    narrative_id: int
    slug: str
    title: str
    body_plain_text: SafeText
    origin: NarrativeOrigin
    generated_at: datetime
    confidence_ratio: float = Field(ge=0, le=1)
    limitations: tuple[str, ...]


class BrowserSafeMarketSourceOut(StrictHistoryModel):
    source_id: str
    display_name: str
    source_type: MarketSourceType
    category: str
    homepage_url: AnyUrl | None = None
    observed_at: datetime | None = None
    limitations: tuple[str, ...] = ()

    @field_validator("homepage_url")
    @classmethod
    def safe_url(cls, value: AnyUrl | None) -> AnyUrl | None:
        if value is None:
            return None
        if value.scheme not in {"https", "http"} or value.username or value.password:
            raise ValueError("source URL is not browser-safe")
        return value
