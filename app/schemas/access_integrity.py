"""Public, secret-free Access Integrity Score 2.0 response schemas."""

from datetime import datetime

from pydantic import BaseModel, Field

from app.domain.access.integrity import (
    AccessIntegrityBand,
    AccessIntegrityRecommendation,
    AccessIntegritySignalCategory,
    AccessIntegritySignalStatus,
)


class AccessIntegritySignalResponse(BaseModel):
    signal_id: str
    category: AccessIntegritySignalCategory
    status: AccessIntegritySignalStatus
    score_delta: float
    maximum_points: float
    evidence_code: str
    explanation: str
    remediation: AccessIntegrityRecommendation
    observed_at: datetime | None = None
    expires_at: datetime | None = None
    evidence_fingerprint: str | None = None
    sensitive_details_redacted: bool = True


class AccessIntegrityCategoryResponse(BaseModel):
    category: AccessIntegritySignalCategory
    earned_points: float = Field(ge=0)
    maximum_points: float = Field(ge=0)
    status: AccessIntegritySignalStatus


class AccessIntegrityRecommendationResponse(BaseModel):
    code: AccessIntegrityRecommendation
    explanation: str


class AccessIntegrityPolicyHintResponse(BaseModel):
    hint: str
    advisory_only: bool = True


class AccessIntegrityScoreResponse(BaseModel):
    version: str
    principal_hash: str
    actor_type: str
    score: int = Field(ge=0, le=100)
    band: AccessIntegrityBand
    confidence: float = Field(ge=0, le=1)
    calculated_at: datetime
    evidence_fresh_until: datetime | None
    categories: list[AccessIntegrityCategoryResponse]
    recommendations: list[AccessIntegrityRecommendationResponse]
    policy_hints: list[AccessIntegrityPolicyHintResponse]
    limitations: list[str]
    crypto_epoch: int
    policy_epoch: int
    schema_epoch: int
