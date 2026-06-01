from __future__ import annotations

from dataclasses import dataclass

from app.db.models.btc_candle import BTCCandle
from app.services.intelligence.historical_similarity_metrics import CONFIDENCE_CALIBRATIONS_TOTAL


@dataclass(frozen=True)
class CalibratedConfidence:
    confidence: float
    reasons: list[str]
    limitations: list[str]


class HistoricalConfidenceCalibrator:
    def calibrate(
        self,
        base_confidence: float,
        sample_size: int,
        consistency_score: float,
        provider_confidence: float = 1.0,
        candle: BTCCandle | None = None,
    ) -> CalibratedConfidence:
        CONFIDENCE_CALIBRATIONS_TOTAL.inc()
        confidence = max(0.0, min(base_confidence, 1.0))
        reasons = [
            f"base_confidence={confidence:.2f}",
            f"sample_size={sample_size}",
            f"consistency={consistency_score:.2f}",
        ]
        limitations = ["Historical similarity does not guarantee future market behavior."]
        if sample_size >= 20:
            confidence += 0.10
            reasons.append("large historical sample increased confidence")
        elif sample_size >= 5:
            confidence += 0.04
            reasons.append("moderate historical sample supported confidence")
        else:
            confidence -= 0.15
            limitations.append("small historical sample size reduced confidence")
        if consistency_score >= 0.70:
            confidence += 0.06
            reasons.append("consistent historical reactions increased confidence")
        elif consistency_score < 0.40:
            confidence -= 0.08
            limitations.append("inconsistent historical reactions reduced confidence")
        if provider_confidence < 0.55:
            confidence -= 0.10
            limitations.append(
                "provider disagreement or low provider confidence reduced confidence"
            )
        if candle is not None and float(candle.provider_disagreement_score or 0.0) > 0.25:
            confidence -= 0.08
            limitations.append("provider disagreement reduced confidence")
        return CalibratedConfidence(
            confidence=max(0.0, min(confidence, 1.0)), reasons=reasons, limitations=limitations
        )
