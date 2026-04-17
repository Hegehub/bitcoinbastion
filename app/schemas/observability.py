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


class OperationsSnapshotOut(BaseModel):
    queue_depth: int
    stale_jobs: int
    providers: list[ProviderHealthOut]
    jobs: JobStatsOut
    deliveries: DeliveryStatsOut
