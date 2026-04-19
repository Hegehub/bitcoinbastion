from pydantic import BaseModel, Field

from app.schemas.common import ExplainabilityOut, FreshnessOut


class FeeRecommendationRequest(BaseModel):
    mempool_congestion: float = Field(ge=0.0, le=1.0)
    target_blocks: int = Field(ge=1, le=72)


class FeeRecommendationResponse(BaseModel):
    suggested_fee_rate_sat_vb: int
    rationale: str
    congestion_state: str
    high_fee_scenario_sat_vb: int
    confidence: float = Field(ge=0.0, le=1.0)
    freshness: FreshnessOut = Field(default_factory=FreshnessOut)
    explainability: ExplainabilityOut = Field(default_factory=ExplainabilityOut)
    data_sources: list[str] = Field(default_factory=list)
