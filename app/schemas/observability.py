from pydantic import BaseModel


class ProviderHealthOut(BaseModel):
    provider: str
    healthy: bool
    details: str


class OperationsSnapshotOut(BaseModel):
    queue_depth: int
    stale_jobs: int
    providers: list[ProviderHealthOut]
