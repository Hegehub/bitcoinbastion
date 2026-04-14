from pydantic import BaseModel, Field


class PrivacyAssessmentRequest(BaseModel):
    reused_addresses: int = Field(default=0, ge=0)
    known_kyc_exposure: bool = False
    utxo_fragmentation_score: float = Field(default=0.0, ge=0.0, le=1.0)


class PrivacyAssessmentResponse(BaseModel):
    risk_score: float = Field(ge=0.0, le=100.0)
    risk_level: str
    recommendations: list[str]
