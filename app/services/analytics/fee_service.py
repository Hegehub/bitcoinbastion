from app.schemas.fees import FeeRecommendationRequest, FeeRecommendationResponse
from app.services.mempool.fee_market_model import FeeMarketModel
from app.services.mempool.mempool_analyzer_service import MempoolAnalyzerService, MempoolSnapshot


class FeeAnalyticsService:
    def recommend(self, payload: FeeRecommendationRequest) -> FeeRecommendationResponse:
        snapshot = MempoolSnapshot(
            backlog_tx_count=max(1, int(200_000 * payload.mempool_congestion) + 20_000),
            backlog_vbytes=max(1, int(140_000_000 * payload.mempool_congestion)),
            median_fee_rate_sat_vb=max(1.0, 2 + payload.mempool_congestion * 60),
            high_priority_fee_rate_sat_vb=max(2.0, 8 + payload.mempool_congestion * 90),
        )
        mempool_state = MempoolAnalyzerService().analyze(snapshot)
        market = FeeMarketModel().estimate(mempool=mempool_state, target_blocks=payload.target_blocks)

        rationale = (
            f"Derived from mempool congestion={payload.mempool_congestion:.2f}, "
            f"state={market.congestion_state}, target_blocks={payload.target_blocks}."
        )
        return FeeRecommendationResponse(
            suggested_fee_rate_sat_vb=market.suggested_fee_rate_sat_vb,
            rationale=rationale,
            congestion_state=market.congestion_state,
            high_fee_scenario_sat_vb=market.high_fee_scenario_sat_vb,
            confidence=market.confidence,
            freshness=market.freshness,
            explainability=market.explainability,
        )
