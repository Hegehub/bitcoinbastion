from fastapi import APIRouter

from app.schemas.base import ResponseEnvelope
from app.schemas.privacy import PrivacyAssessmentRequest, PrivacyAssessmentResponse
from app.services.privacy.privacy_service import PrivacyRiskService

router = APIRouter(prefix="/privacy", tags=["privacy"])


@router.post("/assess", response_model=ResponseEnvelope[PrivacyAssessmentResponse])
def assess_privacy(payload: PrivacyAssessmentRequest) -> ResponseEnvelope[PrivacyAssessmentResponse]:
    result = PrivacyRiskService().assess(payload)
    return ResponseEnvelope(data=result)
