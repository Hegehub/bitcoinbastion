from pydantic import BaseModel


class ProviderHealthOut(BaseModel):
    provider: str
    healthy: bool
    details: str


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


class OperationsSnapshotOut(BaseModel):
    queue_depth: int
    stale_jobs: int
    providers: list[ProviderHealthOut]
    jobs: JobStatsOut
    deliveries: DeliveryStatsOut
    chain_state: ChainStateOut
