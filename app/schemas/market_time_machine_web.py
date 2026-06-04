from __future__ import annotations

from pydantic import BaseModel, Field


class NewsMarkerDTO(BaseModel):
    id: str
    event_id: int | None = None
    candle_id: int | None = None
    title: str
    marker_type: str = "uncertain"
    marker_style: str = "marker-uncertain"
    marker_priority: int = 5
    timestamp: str
    published_at: str = "unknown"
    first_seen: str = "unknown"
    confidence: float = 0.0
    evidence_count: int = 0
    source: str = "unknown"
    sentiment: str = "UNKNOWN"
    btc_relevance: float = 0.0
    source_confidence: float = 0.0
    provider_confidence: float = 0.0
    impact_confidence: float = 0.0
    btc_price_at_publish: float | None = None
    change_15m: float | None = None
    change_1h: float | None = None
    change_4h: float | None = None
    change_24h: float | None = None
    evidence_packet_id: int | None = None
    replay_available: bool = False
    similarity_preview: list[dict[str, object]] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


class CandleAttributionDTO(BaseModel):
    id: int
    timeframe: str
    open_time: str
    close_time: str
    open: float | None = None
    high: float | None = None
    low: float | None = None
    close: float | None = None
    volume: float | None = None
    price_change_pct: float = 0.0
    confidence: float = 0.0
    provider_confidence: float = 0.0
    dominant_direction: str = "neutral"
    volatility_score: float = 0.0
    attribution_count: int = 0
    narrative_strength: float = 0.0
    historical_similarity_count: int = 0
    replay_available: bool = False
    limitations: list[str] = Field(default_factory=list)
    candidate_events: list[dict[str, object]] = Field(default_factory=list)
    candidate_articles: list[dict[str, object]] = Field(default_factory=list)
    candidate_news_events: list[dict[str, object]] = Field(default_factory=list)
    candidate_macro_events: list[dict[str, object]] = Field(default_factory=list)
    candidate_security_events: list[dict[str, object]] = Field(default_factory=list)
    candidate_narrative_events: list[dict[str, object]] = Field(default_factory=list)
    top_attribution: dict[str, object] = Field(default_factory=dict)
    confidence_breakdown: dict[str, object] = Field(default_factory=dict)
    similarity_preview: list[dict[str, object]] = Field(default_factory=list)
    safety_flags: dict[str, object] = Field(default_factory=dict)


class EvidencePanelDTO(BaseModel):
    packet_id: int | None = None
    title: str = "Evidence packet not generated."
    summary: str = ""
    replay_available: bool = False
    evidence_sources: list[dict[str, object]] = Field(default_factory=list)
    provider_confidence: float = 0.0
    source_confidence: float = 0.0
    integrity_status: str = "unknown"
    operator_review_status: str = "not_reviewed"
    limitations: list[str] = Field(default_factory=list)
    evidence_summary: str = ""
    confidence_breakdown: dict[str, object] = Field(default_factory=dict)
    provider_snapshot: dict[str, object] = Field(default_factory=dict)
    source_snapshot: dict[str, object] = Field(default_factory=dict)
    replay_status: str = "unavailable"
    export_json_url: str = ""
    export_markdown_url: str = ""
    relationships_url: str = ""


class ReplaySummaryDTO(BaseModel):
    entity_type: str
    entity_id: int
    replay_available: bool = False
    steps: list[dict[str, object]] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


class SignalCardDTO(BaseModel):
    id: int | None = None
    title: str
    status: str = "draft"
    confidence: float = 0.0
    evidence_count: int = 0
    replay_available: bool = False


class MarketTimelineDTO(BaseModel):
    timeline_items: list[dict[str, object]] = Field(default_factory=list)
    chart_markers: list[NewsMarkerDTO] = Field(default_factory=list)
    candles: list[CandleAttributionDTO] = Field(default_factory=list)
    signals: list[SignalCardDTO] = Field(default_factory=list)
    page: int = 1
    page_size: int = 50
    has_next: bool = False
    filters: dict[str, object] = Field(default_factory=dict)
    limitations: list[str] = Field(default_factory=list)
    evidence_summary: dict[str, object] = Field(default_factory=dict)
    confidence_breakdown: dict[str, object] = Field(default_factory=dict)
    narrative_strength: list[dict[str, object]] = Field(default_factory=list)
    similarity_preview: list[dict[str, object]] = Field(default_factory=list)
    operator_status: dict[str, object] = Field(default_factory=dict)
