from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import ExplainabilityOut, FreshnessOut


class WalletHealthRequest(BaseModel):
    utxo_count: int = Field(ge=0)
    largest_utxo_share: float = Field(ge=0.0, le=1.0)
    avg_fee_rate_sat_vb: float = Field(ge=0.0)
    utxo_values_sats: list[int] = Field(default_factory=list)
    script_hint: str = Field(default="")
    has_descriptor: bool | None = None
    has_recovery_instructions: bool | None = None
    has_backup_reference: bool | None = None


class WalletHealthResponse(BaseModel):
    health_score: float
    utxo_fragmentation_score: float
    privacy_score: float
    fee_exposure_score: float
    recommendations: list[str]
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    explainability: ExplainabilityOut = Field(default_factory=ExplainabilityOut)
    freshness: FreshnessOut = Field(default_factory=FreshnessOut)


class WalletProfileOut(BaseModel):
    id: int
    name: str
    wallet_type: str
    watch_only: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class WalletHealthReportOut(BaseModel):
    id: int
    wallet_profile_id: int
    health_score: float
    utxo_fragmentation_score: float
    privacy_score: float
    fee_exposure_score: float
    recommendations: list[str]
    generated_at: datetime
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    explainability: ExplainabilityOut = Field(default_factory=ExplainabilityOut)
    data_sources: list[str] = Field(default_factory=list)
    freshness: FreshnessOut = Field(default_factory=FreshnessOut)

    model_config = {"from_attributes": True}
