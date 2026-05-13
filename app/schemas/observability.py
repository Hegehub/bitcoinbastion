from pydantic import BaseModel, Field


class ProviderHealthOut(BaseModel):
    provider: str
    healthy: bool
    details: str
    confidence: float = 0.0
    freshness_seconds: int = 0


class DeliveryStatsOut(BaseModel):
    sent_24h: int
    failed_24h: int


class JobStatsOut(BaseModel):
    started_24h: int
    failed_24h: int


class ChainStateOut(BaseModel):
    tip_height: int
    observed_block_height: int
    headers_height: int
    confirmation_depth: int
    reorg_risk_score: float
    finality_score: float
    finality_band: str


class RecoverySLOOut(BaseModel):
    status: str
    target: dict[str, object] = Field(default_factory=dict)
    actual: dict[str, object] = Field(default_factory=dict)
    signals: dict[str, object] = Field(default_factory=dict)
    explainability: dict[str, object] = Field(default_factory=dict)


class OperationsSnapshotOut(BaseModel):
    queue_depth: int
    stale_jobs: int
    providers: list[ProviderHealthOut]
    jobs: JobStatsOut
    deliveries: DeliveryStatsOut
    chain_state: ChainStateOut
    recovery_slo: RecoverySLOOut
