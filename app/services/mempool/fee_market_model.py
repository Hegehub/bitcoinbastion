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
        target = max(1, int(target_blocks))
        urgency = min(12.0, max(1.0, 14 / target))

        if target <= 1:
            band_key = "urgent"
        elif target <= 3:
            band_key = "high"
        elif target <= 8:
            band_key = "medium"
        else:
            band_key = "low"

        band_fee = float(
            mempool.priority_bands.get(band_key, mempool.priority_bands.get("medium", 2.0))
        )

        congestion_multiplier = {
            "low": 0.9,
            "normal": 1.0,
            "elevated": 1.25,
            "congested": 1.55,
            "extreme": 1.95,
        }.get(mempool.congestion_state, 1.1)

        suggested = int(max(1.0, round(band_fee * congestion_multiplier + urgency)))
        high_fee_multiplier = (
            1.6
            if mempool.congestion_state in {"low", "normal"}
            else 1.9 if mempool.congestion_state == "elevated" else 2.2
        )
        stress = int(max(suggested + 1, round(suggested * high_fee_multiplier)))

        freshness_band = str(mempool.freshness.get("freshness_band", "unknown"))
        freshness_penalty = 0.0
        if freshness_band == "recent":
            freshness_penalty = 0.04
        elif freshness_band == "stale":
            freshness_penalty = 0.12
        elif freshness_band == "very_stale":
            freshness_penalty = 0.22

        confidence = max(
            0.3, min(0.95, float(mempool.confidence) - freshness_penalty - min(0.08, urgency / 100))
        )

        return FeeMarketEstimateOut(
            suggested_fee_rate_sat_vb=suggested,
            high_fee_scenario_sat_vb=stress,
            congestion_state=mempool.congestion_state,
            confidence=round(confidence, 3),
            freshness=mempool.freshness,
            explainability={
                "target_blocks": target_blocks,
                "selected_band": band_key,
                "band_fee": band_fee,
                "congestion_multiplier": congestion_multiplier,
                "urgency_component": round(urgency, 3),
                "high_fee_multiplier": high_fee_multiplier,
                "assumptions": [
                    "Recommendation indicates urgency-adjusted fee posture, not a confirmation guarantee.",
                    "High-fee scenario is stress planning guidance for adverse congestion.",
                ],
            },
        )
