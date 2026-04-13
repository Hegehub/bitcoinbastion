from app.schemas.fees import FeeRecommendationRequest, FeeRecommendationResponse


class FeeAnalyticsService:
    def recommend(self, payload: FeeRecommendationRequest) -> FeeRecommendationResponse:
        base = 2
        congestion_component = int(payload.mempool_congestion * 80)
        urgency_component = max(1, int(12 / payload.target_blocks))
        suggested = base + congestion_component + urgency_component
        rationale = (
            f"Calculated from congestion={payload.mempool_congestion:.2f} "
            f"and target_blocks={payload.target_blocks}."
        )
        return FeeRecommendationResponse(suggested_fee_rate_sat_vb=suggested, rationale=rationale)
