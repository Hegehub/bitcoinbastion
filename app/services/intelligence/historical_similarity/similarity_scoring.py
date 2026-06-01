from __future__ import annotations

from dataclasses import dataclass

from app.db.models.historical_event_profile import HistoricalEventProfile


@dataclass(frozen=True)
class SimilarityScore:
    score: float
    band: str
    dimensions: dict[str, float]


class SimilarityScoring:
    weights: dict[str, float] = {
        "event_type": 0.12,
        "sentiment": 0.10,
        "btc_relevance": 0.10,
        "impact_score": 0.10,
        "source_tier": 0.07,
        "narrative_tags": 0.10,
        "market_regime": 0.06,
        "volatility_state": 0.06,
        "time_window": 0.08,
        "security_flag": 0.07,
        "regulatory_flag": 0.07,
        "institutional_flag": 0.07,
    }

    def score_profiles(self, reference: HistoricalEventProfile, candidate: HistoricalEventProfile) -> SimilarityScore:
        dimensions = {
            "event_type": self._exact(reference.event_type, candidate.event_type),
            "sentiment": self._exact(reference.sentiment_label, candidate.sentiment_label),
            "btc_relevance": self._numeric(reference.btc_relevance_score, candidate.btc_relevance_score),
            "impact_score": self._numeric(reference.market_impact_score, candidate.market_impact_score),
            "source_tier": self._source_tier(reference.provider_confidence, candidate.provider_confidence),
            "narrative_tags": self._narrative(reference, candidate),
            "market_regime": 0.5,
            "volatility_state": self._volatility(reference, candidate),
            "time_window": self._time_window(reference, candidate),
            "security_flag": self._flag(reference.security_score, candidate.security_score),
            "regulatory_flag": self._flag(reference.regulatory_score, candidate.regulatory_score),
            "institutional_flag": self._flag(reference.institutional_score, candidate.institutional_score),
        }
        score = round(sum(dimensions[key] * weight for key, weight in self.weights.items()), 6)
        return SimilarityScore(score=score, band=self.band(score), dimensions=dimensions)

    def band(self, value: float) -> str:
        if value < 0.30:
            return "weak"
        if value < 0.60:
            return "moderate"
        if value < 0.80:
            return "strong"
        return "very strong"

    def _exact(self, left: str | None, right: str | None) -> float:
        if not left or not right:
            return 0.5
        return 1.0 if left.strip().lower() == right.strip().lower() else 0.15

    def _numeric(self, left: float | None, right: float | None) -> float:
        if left is None or right is None:
            return 0.5
        return max(0.0, 1.0 - min(abs(float(left) - float(right)), 1.0))

    def _source_tier(self, left: float | None, right: float | None) -> float:
        return self._numeric(self._bucket(left), self._bucket(right))

    def _narrative(self, reference: HistoricalEventProfile, candidate: HistoricalEventProfile) -> float:
        if reference.pattern_type == candidate.pattern_type and reference.pattern_type != "UNKNOWN":
            return 1.0
        if reference.primary_narrative == candidate.primary_narrative:
            return 0.75
        return 0.25

    def _volatility(self, reference: HistoricalEventProfile, candidate: HistoricalEventProfile) -> float:
        return self._numeric(self._max_abs_move(reference), self._max_abs_move(candidate))

    def _time_window(self, reference: HistoricalEventProfile, candidate: HistoricalEventProfile) -> float:
        left = self._dominant_window(reference)
        right = self._dominant_window(candidate)
        if left is None or right is None:
            return 0.5
        if left == right:
            return 1.0
        order = ["15m", "1h", "4h", "24h"]
        return max(0.0, 1.0 - (abs(order.index(left) - order.index(right)) * 0.3))

    def _flag(self, left: float, right: float) -> float:
        return 1.0 if (left >= 0.5) == (right >= 0.5) else 0.2

    def _bucket(self, value: float | None) -> float:
        value = float(value or 0.0)
        if value >= 0.8:
            return 1.0
        if value >= 0.5:
            return 0.5
        return 0.0

    def _max_abs_move(self, profile: HistoricalEventProfile) -> float:
        values = [
            profile.price_change_15m_pct,
            profile.price_change_1h_pct,
            profile.price_change_4h_pct,
            profile.price_change_24h_pct,
        ]
        return max((abs(float(value)) for value in values if value is not None), default=0.0) / 10.0

    def _dominant_window(self, profile: HistoricalEventProfile) -> str | None:
        moves = {
            "15m": profile.price_change_15m_pct,
            "1h": profile.price_change_1h_pct,
            "4h": profile.price_change_4h_pct,
            "24h": profile.price_change_24h_pct,
        }
        present = {key: value for key, value in moves.items() if value is not None}
        if not present:
            return None
        return max(present, key=lambda key: abs(float(present[key] or 0.0)))
