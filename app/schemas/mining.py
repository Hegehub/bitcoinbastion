from datetime import datetime

from pydantic import BaseModel, Field


class MiningWindow(BaseModel):
    window_start: datetime
    window_end: datetime
    resolution: str = Field(description="Window resolution (e.g. 1h, 24h, 7d)")


class HashrateSnapshot(BaseModel):
    window: MiningWindow
    network_hashrate_eh: float
    hashrate_regime: str
    difficulty: float
    difficulty_change_pct: float
    confidence_score: float = Field(ge=0.0, le=1.0)


class PoolShareSnapshot(BaseModel):
    window: MiningWindow
    top_pool_share_pct: float
    top3_pool_share_pct: float
    top5_pool_share_pct: float
    concentration_risk_band: str
    confidence_score: float = Field(ge=0.0, le=1.0)


class BlockProductionSnapshot(BaseModel):
    window: MiningWindow
    expected_blocks: int
    produced_blocks: int
    orphan_rate_pct: float
    empty_block_rate_pct: float
    anomaly_flags: list[str] = Field(default_factory=list)
    confidence_score: float = Field(ge=0.0, le=1.0)


class InclusionCensorshipSnapshot(BaseModel):
    window: MiningWindow
    median_inclusion_delay_blocks: float
    p95_inclusion_delay_blocks: float
    suspected_filter_footprint_score: float = Field(ge=0.0, le=1.0)
    affected_template_classes: list[str] = Field(default_factory=list)
    confidence_score: float = Field(ge=0.0, le=1.0)


class MiningExplainabilityNode(BaseModel):
    key: str
    title: str
    value: float | str | int
    weight: float
    source_refs: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class MiningSovereigntyScorecard(BaseModel):
    window: MiningWindow
    hashrate_resilience_score: float = Field(ge=0.0, le=1.0)
    concentration_risk_score: float = Field(ge=0.0, le=1.0)
    production_integrity_score: float = Field(ge=0.0, le=1.0)
    inclusion_neutrality_score: float = Field(ge=0.0, le=1.0)
    fee_market_alignment_score: float = Field(ge=0.0, le=1.0)
    aggregate_score: float = Field(ge=0.0, le=1.0)
    risk_band: str
    confidence_score: float = Field(ge=0.0, le=1.0)
    explainability_nodes: list[MiningExplainabilityNode] = Field(default_factory=list)
