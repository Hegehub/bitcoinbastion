from pydantic import BaseModel, Field


class FeeRecommendationRequest(BaseModel):
    mempool_congestion: float = Field(ge=0.0, le=1.0)
    target_blocks: int = Field(ge=1, le=72)


class FeeRecommendationResponse(BaseModel):
    suggested_fee_rate_sat_vb: int
    rationale: str
