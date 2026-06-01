from datetime import datetime

from pydantic import BaseModel, Field


class NarrativeItem(BaseModel):
    id: int
    slug: str
    narrative_type: str
    name: str
    display_name: str | None = None
    description: str
    category: str
    is_active: bool = True


class NarrativeSnapshotView(BaseModel):
    snapshot_id: int
    snapshot_time: datetime
    narrative_id: int
    slug: str
    narrative_type: str
    name: str
    display_name: str | None = None
    category: str
    mention_count: int
    weighted_score: float
    heat_score: float
    heat_band: str
    velocity_score: float
    dominance_score: float
    volume_score: float
    growth_score: float
    dominance_pct: float | None = None
    sentiment_score: float
    impact_score: float
    source_count: int
    event_count: int
    supporting_events_count: int
    supporting_articles: list[dict[str, object]] = Field(default_factory=list)
    supporting_events: list[dict[str, object]] = Field(default_factory=list)
    provider_confidence: float
    trend_direction: str
    confidence_score: float
    evidence: dict[str, object] = Field(default_factory=dict)
    limitations: list[str] = Field(default_factory=list)


class NarrativeHeatmapResponse(BaseModel):
    window: str
    snapshot_time: datetime
    top_narratives: list[NarrativeSnapshotView]
    top_rising_narratives: list[NarrativeSnapshotView]
    top_falling_narratives: list[NarrativeSnapshotView]
    highest_impact_narratives: list[NarrativeSnapshotView]
    dominance_index: dict[str, float]
    limitations: list[str]
    generated_at: datetime
