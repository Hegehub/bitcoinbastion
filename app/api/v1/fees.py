from fastapi import APIRouter

from app.schemas.base import ResponseEnvelope
from app.schemas.fees import FeeRecommendationRequest, FeeRecommendationResponse
from app.services.analytics.fee_service import FeeAnalyticsService

router = APIRouter(prefix="/fees", tags=["fees"])


@router.post("/recommendation", response_model=ResponseEnvelope[FeeRecommendationResponse])
def fee_recommendation(payload: FeeRecommendationRequest) -> ResponseEnvelope[FeeRecommendationResponse]:
    result = FeeAnalyticsService().recommend(payload)
    return ResponseEnvelope(data=result)
