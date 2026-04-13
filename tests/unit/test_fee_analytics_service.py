from app.schemas.fees import FeeRecommendationRequest
from app.services.analytics.fee_service import FeeAnalyticsService


def test_fee_recommendation_increases_with_congestion() -> None:
    service = FeeAnalyticsService()
    low = service.recommend(FeeRecommendationRequest(mempool_congestion=0.1, target_blocks=6))
    high = service.recommend(FeeRecommendationRequest(mempool_congestion=0.9, target_blocks=6))
    assert high.suggested_fee_rate_sat_vb > low.suggested_fee_rate_sat_vb
