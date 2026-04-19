from pydantic import BaseModel, Field

from app.services.mempool.mempool_analyzer_service import MempoolStateOut


class FeeMarketEstimateOut(BaseModel):
    suggested_fee_rate_sat_vb: int
    high_fee_scenario_sat_vb: int
    congestion_state: str
    confidence: float = Field(ge=0.0, le=1.0)
    freshness: dict[str, object]
    explainability: dict[str, object]


class FeeMarketModel:
    def estimate(self, *, mempool: MempoolStateOut, target_blocks: int) -> FeeMarketEstimateOut:
        urgency = max(1.0, 12 / max(1, target_blocks))
        band_key = "high" if target_blocks <= 2 else "medium" if target_blocks <= 6 else "low"
        band_fee = mempool.priority_bands.get(band_key, mempool.priority_bands.get("medium", 2.0))

        multiplier = 1.0
        if mempool.congestion_state == "elevated":
            multiplier = 1.2
        elif mempool.congestion_state == "severe":
            multiplier = 1.5

        suggested = int(max(1.0, band_fee * multiplier + urgency))
        stress = int(max(suggested, suggested * 1.8))

        return FeeMarketEstimateOut(
            suggested_fee_rate_sat_vb=suggested,
            high_fee_scenario_sat_vb=stress,
            congestion_state=mempool.congestion_state,
            confidence=0.74,
            freshness=mempool.freshness,
            explainability={
                "target_blocks": target_blocks,
                "selected_band": band_key,
                "band_fee": band_fee,
                "congestion_multiplier": multiplier,
                "urgency_component": urgency,
            },
        )
