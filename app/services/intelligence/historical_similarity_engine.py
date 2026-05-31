from __future__ import annotations

from dataclasses import dataclass
from statistics import mean, median
from typing import Any

from sqlalchemy.orm import Session

from app.db.models.historical_event_similarity import HistoricalEventSimilarity
from app.db.models.news_event import NewsEvent
from app.db.models.news_price_impact import NewsPriceImpact
from app.db.models.time_utils import utcnow
from app.services.intelligence.historical_confidence_calibrator import (
    HistoricalConfidenceCalibrator,
)
from app.services.intelligence.historical_similarity_metrics import (
    SIMILARITY_CALCULATIONS_TOTAL,
    SIMILARITY_FAILURES_TOTAL,
)
from app.services.intelligence.market_memory_service import (
    MarketMemoryService,
    PatternCandidate,
)

HISTORICAL_SIMILARITY_DISCLAIMER = (
    "Historical similarity does not guarantee future market behavior."
)
CORRELATION_DISCLAIMER = "Correlation-based analysis is not proof of causation."


@dataclass(frozen=True)
class EventSimilarityScore:
    score: float
    components: dict[str, float]
    reasons: list[str]
    limitations: list[str]


class HistoricalSimilarityEngine:
    """Deterministic market-memory similarity engine for NewsEvent analogs.

    The engine intentionally compares evidence and historical reaction profiles. It does
    not predict price moves and always returns limitations with the mandatory historical
    similarity disclaimer.
    """

    def __init__(self, db: Session) -> None:
        self.db = db
        self.memory = MarketMemoryService(db)
        self.calibrator = HistoricalConfidenceCalibrator()

    def find_similar_events(self, event_id: int, limit: int = 10) -> dict[str, Any]:
        try:
            SIMILARITY_CALCULATIONS_TOTAL.inc()
            reference = self.db.get(NewsEvent, event_id)
            if reference is None:
                return self._empty_response(event_id, "reference_event_not_found")

            reference_patterns = self.memory.classify_event(reference)
            candidates = (
                self.db.query(NewsEvent)
                .filter(NewsEvent.id != event_id)
                .order_by(NewsEvent.first_seen_at.desc(), NewsEvent.id.desc())
                .all()
            )
            scored: list[tuple[NewsEvent, EventSimilarityScore]] = []
            for candidate in candidates:
                candidate_patterns = self.memory.classify_event(candidate)
                score = self.score_event_pair(
                    reference, candidate, reference_patterns, candidate_patterns
                )
                if score.score > 0.0:
                    scored.append((candidate, score))
            scored.sort(key=lambda item: (item[1].score, item[0].first_seen_at), reverse=True)
            top = scored[:limit]
            self._persist_results(reference.id, top)

            impacts: list[NewsPriceImpact] = []
            for item, _ in top:
                impact = self._impact_for(item.id)
                if impact is not None:
                    impacts.append(impact)
            summary = self._reaction_summary(impacts)
            consistency = self._reaction_consistency(impacts)
            provider_confidence = self._provider_confidence(reference, impacts)
            base_confidence = mean([score.score for _, score in top]) if top else 0.0
            calibrated = self.calibrator.calibrate(
                base_confidence=base_confidence,
                sample_size=len(top),
                consistency_score=consistency,
                provider_confidence=provider_confidence,
            )
            limitations = self._limitations(len(top), calibrated.limitations)
            response = {
                "current_event": self._event_payload(reference),
                "pattern_reasoning": [self._pattern_payload(item) for item in reference_patterns],
                "similar_events": [
                    self._similar_event_payload(candidate, score) for candidate, score in top
                ],
                "sample_size": len(top),
                "historical_reaction_profile": summary,
                "confidence": calibrated.confidence,
                "confidence_reasoning": calibrated.reasons,
                "limitations": limitations,
                "provider_confidence": provider_confidence,
                "evidence": {
                    "pattern_classification": [
                        self._pattern_payload(item) for item in reference_patterns
                    ],
                    "candidate_event_count": len(candidates),
                    "persisted_similarity_count": len(top),
                    "reaction_statistics": summary,
                    "disclaimer": HISTORICAL_SIMILARITY_DISCLAIMER,
                },
                "generated_at": utcnow(),
            }
            return response
        except Exception:
            SIMILARITY_FAILURES_TOTAL.inc()
            raise

    def score_event_pair(
        self,
        reference: NewsEvent,
        candidate: NewsEvent,
        reference_patterns: list[PatternCandidate] | None = None,
        candidate_patterns: list[PatternCandidate] | None = None,
    ) -> EventSimilarityScore:
        reference_patterns = reference_patterns or self.memory.classify_event(
            reference, persist=False
        )
        candidate_patterns = candidate_patterns or self.memory.classify_event(
            candidate, persist=False
        )
        reference_impact = self._impact_for(reference.id)
        candidate_impact = self._impact_for(candidate.id)

        components = {
            "pattern": self._pattern_overlap(reference_patterns, candidate_patterns),
            "sentiment": self._sentiment_similarity(
                reference.event_sentiment, candidate.event_sentiment
            ),
            "btc_relevance": self._numeric_similarity(
                reference.btc_relevance_score, candidate.btc_relevance_score
            ),
            "impact_profile": self._numeric_similarity(
                reference.market_impact_score, candidate.market_impact_score
            ),
            "volatility": self._volatility_similarity(reference_impact, candidate_impact),
            "market_direction": self._direction_similarity(reference_impact, candidate_impact),
            "source_profile": self._source_similarity(reference, candidate),
            "institutional": self._flag_similarity(
                reference.is_institutional_related, candidate.is_institutional_related
            ),
            "regulatory": self._flag_similarity(
                reference.is_regulatory_related, candidate.is_regulatory_related
            ),
            "security": self._flag_similarity(
                reference.is_security_related, candidate.is_security_related
            ),
            "macro": self._flag_similarity(reference.is_macro_related, candidate.is_macro_related),
        }
        score = (
            components["pattern"] * 0.24
            + components["sentiment"] * 0.12
            + components["btc_relevance"] * 0.10
            + components["impact_profile"] * 0.12
            + components["volatility"] * 0.08
            + components["market_direction"] * 0.08
            + components["source_profile"] * 0.08
            + components["institutional"] * 0.05
            + components["regulatory"] * 0.05
            + components["security"] * 0.04
            + components["macro"] * 0.04
        )
        reasons = self._score_reasons(components)
        limitations = [HISTORICAL_SIMILARITY_DISCLAIMER, CORRELATION_DISCLAIMER]
        if components["pattern"] < 0.5:
            limitations.append("No high-confidence shared pattern was identified.")
        if components["volatility"] < 0.5:
            limitations.append("Historical volatility context differs.")
        return EventSimilarityScore(
            round(max(0.0, min(1.0, score)), 6), components, reasons, limitations
        )

    def _persist_results(
        self, event_id: int, rows: list[tuple[NewsEvent, EventSimilarityScore]]
    ) -> None:
        self.db.query(HistoricalEventSimilarity).filter(
            HistoricalEventSimilarity.event_id == event_id
        ).delete()
        for candidate, score in rows:
            self.db.add(
                HistoricalEventSimilarity(
                    event_id=event_id,
                    similar_event_id=candidate.id,
                    similarity_score=score.score,
                    pattern_match=score.components["pattern"] >= 0.75,
                    sentiment_match=score.components["sentiment"],
                    impact_match=score.components["impact_profile"],
                    volatility_match=score.components["volatility"],
                    explanation_json={
                        "reasons": score.reasons,
                        "components": score.components,
                        "limitations": score.limitations,
                        "disclaimer": HISTORICAL_SIMILARITY_DISCLAIMER,
                    },
                )
            )
        self.db.flush()

    def _empty_response(self, event_id: int, reason: str) -> dict[str, Any]:
        return {
            "current_event": {"event_id": event_id},
            "pattern_reasoning": [],
            "similar_events": [],
            "sample_size": 0,
            "historical_reaction_profile": self._reaction_summary([]),
            "confidence": 0.0,
            "confidence_reasoning": [],
            "limitations": [HISTORICAL_SIMILARITY_DISCLAIMER, CORRELATION_DISCLAIMER, reason],
            "provider_confidence": 0.0,
            "evidence": {
                "candidate_event_count": 0,
                "disclaimer": HISTORICAL_SIMILARITY_DISCLAIMER,
            },
            "generated_at": utcnow(),
        }

    def _impact_for(self, event_id: int | None) -> NewsPriceImpact | None:
        if event_id is None:
            return None
        return self.db.query(NewsPriceImpact).filter(NewsPriceImpact.event_id == event_id).first()

    def _pattern_overlap(
        self, left: list[PatternCandidate], right: list[PatternCandidate]
    ) -> float:
        left_slugs = {item.pattern.slug: item.confidence for item in left}
        right_slugs = {item.pattern.slug: item.confidence for item in right}
        overlap = set(left_slugs).intersection(right_slugs)
        if overlap:
            return max(min(left_slugs[slug], right_slugs[slug]) for slug in overlap)
        left_categories = {item.pattern.category for item in left}
        right_categories = {item.pattern.category for item in right}
        if left_categories.intersection(right_categories):
            return 0.45
        return 0.0

    def _sentiment_similarity(self, left: str | None, right: str | None) -> float:
        left_value = (left or "UNKNOWN").upper()
        right_value = (right or "UNKNOWN").upper()
        if left_value == right_value:
            return 1.0
        if "UNKNOWN" in {left_value, right_value} or "NEUTRAL" in {left_value, right_value}:
            return 0.45
        return 0.1

    def _numeric_similarity(self, left: float | None, right: float | None) -> float:
        return round(max(0.0, 1.0 - min(abs((left or 0.0) - (right or 0.0)), 1.0)), 6)

    def _volatility_similarity(
        self, left: NewsPriceImpact | None, right: NewsPriceImpact | None
    ) -> float:
        if left is None or right is None:
            return 0.5
        return self._numeric_similarity(left.volatility_context, right.volatility_context)

    def _direction_similarity(
        self, left: NewsPriceImpact | None, right: NewsPriceImpact | None
    ) -> float:
        if left is None or right is None:
            return 0.5
        left_direction = self._dominant_direction(left)
        right_direction = self._dominant_direction(right)
        if left_direction == right_direction:
            return 1.0
        if "UNKNOWN" in {left_direction, right_direction}:
            return 0.45
        return 0.05

    def _dominant_direction(self, impact: NewsPriceImpact) -> str:
        if impact.actual_direction and impact.actual_direction.upper() != "UNKNOWN":
            return impact.actual_direction.upper()
        values = [
            impact.change_15m_pct,
            impact.change_1h_pct,
            impact.change_4h_pct,
            impact.change_24h_pct,
        ]
        numeric = [value for value in values if value is not None]
        if not numeric:
            return "UNKNOWN"
        total = sum(numeric)
        if total > 0:
            return "UP"
        if total < 0:
            return "DOWN"
        return "FLAT"

    def _source_similarity(self, left: NewsEvent, right: NewsEvent) -> float:
        source_count_similarity = 1.0 - min(
            abs((left.source_count or 0) - (right.source_count or 0)) / 5.0, 1.0
        )
        provider_similarity = self._numeric_similarity(
            left.provider_confidence, right.provider_confidence
        )
        return round((source_count_similarity * 0.5) + (provider_similarity * 0.5), 6)

    def _flag_similarity(self, left: bool, right: bool) -> float:
        return 1.0 if bool(left) == bool(right) else 0.0

    def _score_reasons(self, components: dict[str, float]) -> list[str]:
        labels = {
            "pattern": "shared market pattern",
            "sentiment": "similar sentiment",
            "btc_relevance": "similar BTC relevance",
            "impact_profile": "similar impact profile",
            "volatility": "similar volatility context",
            "market_direction": "similar historical market direction",
            "source_profile": "similar source/provider profile",
            "institutional": "institutional context alignment",
            "regulatory": "regulatory context alignment",
            "security": "security context alignment",
            "macro": "macro context alignment",
        }
        return [labels[key] for key, value in components.items() if value >= 0.75] or [
            "limited but non-zero evidence overlap"
        ]

    def _reaction_summary(self, impacts: list[NewsPriceImpact]) -> dict[str, Any]:
        return {
            "sample_size": len(impacts),
            "median": {
                "15m": self._median([impact.change_15m_pct for impact in impacts]),
                "1h": self._median([impact.change_1h_pct for impact in impacts]),
                "4h": self._median([impact.change_4h_pct for impact in impacts]),
                "24h": self._median([impact.change_24h_pct for impact in impacts]),
            },
            "average": {
                "15m": self._average([impact.change_15m_pct for impact in impacts]),
                "1h": self._average([impact.change_1h_pct for impact in impacts]),
                "4h": self._average([impact.change_4h_pct for impact in impacts]),
                "24h": self._average([impact.change_24h_pct for impact in impacts]),
            },
            "positive_ratio": self._ratio(impacts, positive=True),
            "negative_ratio": self._ratio(impacts, positive=False),
        }

    def _reaction_consistency(self, impacts: list[NewsPriceImpact]) -> float:
        if not impacts:
            return 0.0
        positive_ratio = self._ratio(impacts, positive=True)
        negative_ratio = self._ratio(impacts, positive=False)
        return max(positive_ratio, negative_ratio)

    def _provider_confidence(self, reference: NewsEvent, impacts: list[NewsPriceImpact]) -> float:
        values = [reference.provider_confidence]
        values.extend(impact.provider_confidence for impact in impacts)
        numeric = [value for value in values if value is not None]
        if not numeric:
            return 0.0
        return round(max(0.0, min(1.0, mean(numeric))), 6)

    def _ratio(self, impacts: list[NewsPriceImpact], *, positive: bool) -> float:
        values = [impact.change_4h_pct for impact in impacts if impact.change_4h_pct is not None]
        if not values:
            return 0.0
        matches = [value for value in values if (value > 0 if positive else value < 0)]
        return round(len(matches) / len(values), 6)

    def _median(self, values: list[float | None]) -> float | None:
        numeric = [value for value in values if value is not None]
        if not numeric:
            return None
        return round(float(median(numeric)), 6)

    def _average(self, values: list[float | None]) -> float | None:
        numeric = [value for value in values if value is not None]
        if not numeric:
            return None
        return round(float(mean(numeric)), 6)

    def _event_payload(self, event: NewsEvent) -> dict[str, Any]:
        return {
            "event_id": event.id,
            "title": event.canonical_title,
            "event_type": event.event_type,
            "event_category": event.event_category,
            "sentiment": event.event_sentiment,
            "btc_relevance_score": event.btc_relevance_score,
            "market_impact_score": event.market_impact_score,
            "first_seen_at": event.first_seen_at,
        }

    def _pattern_payload(self, candidate: PatternCandidate) -> dict[str, Any]:
        return {
            "pattern_id": candidate.pattern.id,
            "slug": candidate.pattern.slug,
            "name": candidate.pattern.name,
            "category": candidate.pattern.category,
            "confidence": candidate.confidence,
            "reasons": candidate.reasons,
        }

    def _similar_event_payload(
        self, event: NewsEvent, score: EventSimilarityScore
    ) -> dict[str, Any]:
        impact = self._impact_for(event.id)
        return {
            "event_id": event.id,
            "title": event.canonical_title,
            "date": event.first_seen_at,
            "similarity_score": score.score,
            "similarity_band": self._band(score.score),
            "reaction_15m_pct": impact.change_15m_pct if impact else None,
            "reaction_1h_pct": impact.change_1h_pct if impact else None,
            "reaction_4h_pct": impact.change_4h_pct if impact else None,
            "reaction_24h_pct": impact.change_24h_pct if impact else None,
            "confidence": min(score.score, event.event_confidence or score.score),
            "summary": "; ".join(score.reasons),
            "explanation": {"reasons": score.reasons, "components": score.components},
            "limitations": score.limitations,
        }

    def _band(self, score: float) -> str:
        if score >= 0.8:
            return "very_strong"
        if score >= 0.6:
            return "strong"
        if score >= 0.3:
            return "moderate"
        return "weak"

    def _limitations(self, sample_size: int, calibrated_limitations: list[str]) -> list[str]:
        limitations = [HISTORICAL_SIMILARITY_DISCLAIMER, CORRELATION_DISCLAIMER]
        if sample_size == 0:
            limitations.append("No historical analogs were available for this event.")
        elif sample_size < 5:
            limitations.append("Small historical sample size limits confidence.")
        limitations.extend(item for item in calibrated_limitations if item not in limitations)
        return limitations
