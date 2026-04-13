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
