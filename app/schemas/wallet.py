from datetime import datetime

from pydantic import BaseModel, Field


class WalletHealthRequest(BaseModel):
    utxo_count: int = Field(ge=0)
    largest_utxo_share: float = Field(ge=0.0, le=1.0)
    avg_fee_rate_sat_vb: float = Field(ge=0.0)


class WalletHealthResponse(BaseModel):
    health_score: float
    utxo_fragmentation_score: float
    privacy_score: float
    fee_exposure_score: float
    recommendations: list[str]


class WalletProfileOut(BaseModel):
    id: int
    name: str
    wallet_type: str
    watch_only: bool
    created_at: datetime

    model_config = {"from_attributes": True}
