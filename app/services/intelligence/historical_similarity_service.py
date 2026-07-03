from __future__ import annotations

from dataclasses import dataclass
from statistics import mean, median
from typing import Iterable

from sqlalchemy.orm import Session

from app.db.models.candle_attribution import CandleAttribution
from app.db.models.historical_event_profile import HistoricalEventProfile
from app.db.models.historical_similarity_match import HistoricalSimilarityMatch
from app.db.models.historical_similarity_record import HistoricalSimilarityRecord
from app.db.models.historical_reaction_statistics import HistoricalReactionStatistics
from app.db.models.historical_similarity_result import HistoricalSimilarityResult
from app.db.models.market_pattern import MarketPattern as MarketPatternModel
from app.db.models.market_pattern_library import MarketPatternLibrary
from app.db.models.pattern_occurrence import PatternOccurrence
from app.db.models.pattern_reaction_snapshot import PatternReactionSnapshot
from app.db.models.news_event import NewsEvent
from app.db.models.news_price_impact import NewsPriceImpact
from app.schemas.historical_similarity import HistoricalSimilarityReport
from app.services.intelligence.historical_similarity_metrics import (
    HISTORICAL_SIMILARITY_FAILURES_TOTAL,
    HISTORICAL_SIMILARITY_MATCHES_TOTAL,
    HISTORICAL_SIMILARITY_RUNS_TOTAL,
    PATTERN_OCCURRENCES_TOTAL,
    PATTERN_STATISTICS_UPDATES_TOTAL,
)
from app.services.intelligence.historical_profile_builder import HistoricalEventProfileBuilder
from app.services.intelligence.market_memory_service import MarketMemoryService
from app.services.intelligence.pattern_confidence_service import PatternConfidenceService
from app.services.intelligence.pattern_classification_service import PatternClassificationService

CORRELATION_LIMITATION = "Correlation is not proof of causation."
PAST_PERFORMANCE_LIMITATION = "Past reactions do not guarantee future market behavior."
HISTORICAL_OUTCOME_LIMITATION = "Historical similarity does not guarantee future outcomes."
REQUIRED_LIMITATIONS = [
    "historical_similarity_not_prediction",
    "historical_sample_count_low",
    "pattern_confidence_low",
    "provider_diversity_low",
    "market_structure_changed",
    "historical_reference_only",
    "not_financial_advice",
    "sample_size_limited",
    "market_regime_changed",
    "provider_limitations",
    "correlation_not_causation",
    "historical_context_only",
    "not_prediction",
    "evidence_based",
]


@dataclass(frozen=True)
class SimilarityComponents:
    event_type_match: float
    narrative_similarity: float
    sentiment_similarity: float
    impact_similarity: float
    price_behavior_similarity: float
    confidence_similarity: float
    time_window_similarity: float

    @property
    def final_score(self) -> float:
        score = (
            self.event_type_match * 0.25
            + self.sentiment_similarity * 0.15
            + self.narrative_similarity * 0.20
            + self.impact_similarity * 0.15
            + self.price_behavior_similarity * 0.15
            + self.confidence_similarity * 0.10
            + self.time_window_similarity * 0.10
        )
        return round(max(0.0, min(1.0, score)), 6)


class HistoricalSimilarityService:
    """Explainable, replay-safe comparisons between current and historical events.

    This service intentionally produces correlation-oriented comparisons only. It never
    predicts future BTC movement and always emits limitations that distinguish market
    memory from causation claims.
    """

    def __init__(self, db: Session) -> None:
        self.db = db
        self.profile_builder = HistoricalEventProfileBuilder(db)

    def classify_event(self, event: NewsEvent) -> list[dict[str, object]]:
        return PatternClassificationService(self.db).classify_market_patterns(event)

    def score_similarity(
        self, reference_event_id: int, candidate_event_id: int
    ) -> dict[str, object]:
        reference = self.db.get(NewsEvent, reference_event_id)
        candidate = self.db.get(NewsEvent, candidate_event_id)
        if reference is None or candidate is None:
            return {
                "similarity_score": 0.0,
                "similarity_band": self.similarity_band(0.0),
                "explanation": {},
            }
        reference_profile = self._ensure_profile_for_event(reference)
        candidate_profile = self._ensure_profile_for_event(candidate)
        components = self._score_components(reference_profile, candidate_profile)
        return {
            "similarity_score": components.final_score,
            "similarity_band": self.similarity_band(components.final_score),
            "explanation": self._build_explanation(
                reference_profile, candidate_profile, components
            ),
        }

    def build_historical_context(self, event_id: int, limit: int = 10) -> dict[str, object]:
        report = self.build_event_report(event_id, limit=limit)
        matches = list(report.similar_events)
        reference_event = report.reference_event or {}
        return {
            "current_event": reference_event,
            "pattern_name": (matches[0].get("pattern_type") if matches else None),
            "pattern_category": self._pattern_category(
                matches[0].get("pattern_type") if matches else None
            ),
            "similarity_score": matches[0].get("similarity_score") if matches else 0.0,
            "similarity_band": (
                self._band_label(float(matches[0].get("similarity_score", 0.0)))
                if matches
                else "VERY_LOW"
            ),
            "historical_matches": matches,
            "historical_examples": matches,
            "matched_pattern": (matches[0].get("pattern_type") if matches else None),
            "confidence_breakdown": (matches[0].get("confidence_breakdown") if matches else {}),
            "narrative_tags": self._narrative_tags(reference_event),
            "provider_confidence": reference_event.get("provider_confidence", report.confidence),
            "historical_median": {
                "15m": report.median_reaction_15m,
                "1h": report.median_reaction_1h,
                "4h": report.median_reaction_4h,
                "24h": report.median_reaction_24h,
            },
            "historical_average": {
                "15m": report.average_reaction_15m,
                "1h": report.average_reaction_1h,
                "4h": report.average_reaction_4h,
                "24h": report.average_reaction_24h,
            },
            "pattern_confidence": report.confidence,
            "reaction_statistics": report.evidence.get("reaction_statistics", {}),
            "limitations": self._limitations(report.limitations),
            "safety": [
                "historical_context_only",
                "not_prediction",
                "correlation_not_causation",
                "evidence_based",
            ],
        }

    def calculate_pattern_confidence(self, pattern_id: int) -> dict[str, float]:
        return PatternConfidenceService(self.db).calculate(pattern_id).as_dict()

    def rank_similar_events(
        self, reference_event_id: int, limit: int = 10
    ) -> list[dict[str, object]]:
        return self.find_similar_events(reference_event_id, limit=limit)

    def calculate_similarity_score(
        self, reference_event_id: int, candidate_event_id: int
    ) -> dict[str, object]:
        return self.score_similarity(reference_event_id, candidate_event_id)

    def build_reaction_statistics(self, pattern_id: int) -> dict[str, object]:
        pattern = self.db.get(MarketPatternModel, pattern_id)
        if pattern is None:
            return {"pattern_id": pattern_id, "samples": 0}
        event_ids = [
            row.event_id
            for row in self.db.query(PatternOccurrence)
            .filter(PatternOccurrence.pattern_id == pattern_id)
            .all()
            if row.event_id is not None
        ]
        impacts = (
            self.db.query(NewsPriceImpact)
            .filter(NewsPriceImpact.event_id.in_(event_ids or [0]))
            .all()
        )

        def vals(attr: str) -> list[float]:
            return [
                float(getattr(impact, attr))
                for impact in impacts
                if getattr(impact, attr) is not None
            ]

        moves_4h = vals("change_4h_pct") or vals("change_1h_pct") or vals("change_15m_pct")
        samples = len(impacts)
        positive = sum(1 for value in moves_4h if value > 0)
        negative = sum(1 for value in moves_4h if value < 0)
        neutral = max(0, samples - positive - negative)
        row = (
            self.db.query(HistoricalReactionStatistics)
            .filter(HistoricalReactionStatistics.pattern_id == pattern_id)
            .first()
        )
        if row is None:
            row = HistoricalReactionStatistics(pattern_id=pattern_id)
            self.db.add(row)
        row.samples = samples
        row.median_move_15m = self._median_or_none(vals("change_15m_pct"))
        row.median_move_1h = self._median_or_none(vals("change_1h_pct"))
        row.median_move_4h = self._median_or_none(vals("change_4h_pct"))
        row.median_move_24h = self._median_or_none(vals("change_24h_pct"))
        row.positive_ratio = round(positive / samples, 6) if samples else 0.0
        row.negative_ratio = round(negative / samples, 6) if samples else 0.0
        row.neutral_ratio = round(neutral / samples, 6) if samples else 0.0
        self.db.flush()
        PATTERN_STATISTICS_UPDATES_TOTAL.inc()
        return self._reaction_statistics_payload(row)

    def build_similarity_evidence(self, event_id: int, limit: int = 5) -> dict[str, object]:
        context = self.build_historical_context(event_id, limit=limit)
        top_pattern_id = None
        matches = context.get("historical_matches", [])
        if isinstance(matches, list) and matches:
            top_pattern_id = self._market_pattern_id(matches[0].get("pattern_type"))
        stats = (
            self.build_reaction_statistics(top_pattern_id)
            if top_pattern_id is not None
            else {"samples": 0}
        )
        return {
            "matched_pattern": context.get("matched_pattern"),
            "matching_factors": context.get("confidence_breakdown"),
            "reaction_statistics": stats,
            "provider_confidence": context.get("provider_confidence", 0.0),
            "limitations": context.get("limitations", []),
            "historical_samples_used": len(matches) if isinstance(matches, list) else 0,
            "safety": [
                "historical_reference_only",
                "correlation_not_causation",
                "not_financial_advice",
                "evidence_based",
            ],
        }

    def find_similar_events(
        self, reference_event_id: int, limit: int = 10, persist_results: bool = True
    ) -> list[dict[str, object]]:
        reference_event = self.db.get(NewsEvent, reference_event_id)
        if reference_event is None:
            return []
        reference_profile = self._ensure_profile_for_event(reference_event)
        candidate_profiles = self._candidate_profiles(exclude_event_id=reference_event_id)
        results = self._rank_profiles(
            reference_profile, candidate_profiles, limit=limit, persist_results=persist_results
        )
        if results:
            HISTORICAL_SIMILARITY_MATCHES_TOTAL.inc(len(results))
        return results

    def find_similar_news_events(
        self, event_id: int, limit: int = 10, persist_results: bool = True
    ) -> list[dict[str, object]]:
        return self.find_similar_events(event_id, limit=limit, persist_results=persist_results)

    def find_similar_candle_events(
        self, candle_id: int, limit: int = 10, persist_results: bool = True
    ) -> list[dict[str, object]]:
        attribution = (
            self.db.query(CandleAttribution)
            .filter(CandleAttribution.candle_id == candle_id)
            .order_by(
                CandleAttribution.confidence_score.desc(),
                CandleAttribution.rank.asc(),
                CandleAttribution.id.asc(),
            )
            .first()
        )
        if attribution is None:
            return []
        if attribution.event_id is not None:
            return self.find_similar_events(
                attribution.event_id, limit=limit, persist_results=persist_results
            )
        reference_profile = self.profile_builder.build_from_candle_attribution(attribution)
        candidate_profiles = self._candidate_profiles(exclude_event_id=None)
        return self._rank_profiles(
            reference_profile, candidate_profiles, limit=limit, persist_results=persist_results
        )

    def find_similar_security_events(
        self, event_id: int, limit: int = 10, persist_results: bool = True
    ) -> list[dict[str, object]]:
        reference_event = self.db.get(NewsEvent, event_id)
        if reference_event is None:
            return []
        reference_profile = self._ensure_profile_for_event(reference_event)
        candidates = [
            profile
            for profile in self._candidate_profiles(exclude_event_id=event_id)
            if profile.security_score >= 0.5
        ]
        return self._rank_profiles(
            reference_profile, candidates, limit=limit, persist_results=persist_results
        )

    def find_similar_regulatory_events(
        self, event_id: int, limit: int = 10, persist_results: bool = True
    ) -> list[dict[str, object]]:
        reference_event = self.db.get(NewsEvent, event_id)
        if reference_event is None:
            return []
        reference_profile = self._ensure_profile_for_event(reference_event)
        candidates = [
            profile
            for profile in self._candidate_profiles(exclude_event_id=event_id)
            if profile.regulatory_score >= 0.5
        ]
        return self._rank_profiles(
            reference_profile, candidates, limit=limit, persist_results=persist_results
        )

    def evidence_packet_for_event(self, event_id: int, limit: int = 3) -> dict[str, object]:
        similar_events = self.find_similar_events(event_id, limit=limit, persist_results=False)
        return {
            "similar_historical_events": [
                {
                    "event_id": row.get("event_id"),
                    "title": row.get("title"),
                    "pattern_type": row.get("pattern_type"),
                    "similarity": row.get("similarity_score"),
                    "reaction_4h_pct": row.get("reaction_4h"),
                }
                for row in similar_events
            ],
            "historical_similarity_summary": self._summary(similar_events),
            "limitations": [
                CORRELATION_LIMITATION,
                PAST_PERFORMANCE_LIMITATION,
                HISTORICAL_OUTCOME_LIMITATION,
            ],
        }

    def build_event_report(self, event_id: int, limit: int = 10) -> HistoricalSimilarityReport:
        try:
            HISTORICAL_SIMILARITY_RUNS_TOTAL.inc()
            event = self.db.get(NewsEvent, event_id)
            if event is None:
                return self._empty_report({"event_id": event_id})
            classifications = PatternClassificationService(self.db).classification_evidence(event)
            similar_events = self.find_similar_events(event_id, limit=limit)
            return self._report_for_event(event, similar_events, classifications)
        except Exception:
            HISTORICAL_SIMILARITY_FAILURES_TOTAL.inc()
            raise

    def build_article_report(self, article_id: int, limit: int = 10) -> HistoricalSimilarityReport:
        try:
            HISTORICAL_SIMILARITY_RUNS_TOTAL.inc()
            event = (
                self.db.query(NewsEvent)
                .filter(NewsEvent.primary_article_id == article_id)
                .order_by(NewsEvent.id.desc())
                .first()
            )
            if event is None:
                impact = (
                    self.db.query(NewsPriceImpact)
                    .filter(NewsPriceImpact.article_id == article_id)
                    .order_by(NewsPriceImpact.id.desc())
                    .first()
                )
                event = (
                    self.db.get(NewsEvent, impact.event_id) if impact and impact.event_id else None
                )
            if event is None:
                return self._empty_report({"article_id": article_id})
            classifications = PatternClassificationService(self.db).classification_evidence(event)
            similar_events = self.find_similar_events(event.id, limit=limit)
            return self._report_for_event(event, similar_events, classifications)
        except Exception:
            HISTORICAL_SIMILARITY_FAILURES_TOTAL.inc()
            raise

    def list_patterns(self) -> list[MarketPatternLibrary]:
        return PatternClassificationService(self.db).ensure_pattern_library()

    def get_pattern(self, pattern_code: str) -> MarketPatternLibrary | None:
        PatternClassificationService(self.db).ensure_pattern_library()
        return (
            self.db.query(MarketPatternLibrary)
            .filter(MarketPatternLibrary.pattern_code == pattern_code)
            .first()
        )

    def _candidate_profiles(self, exclude_event_id: int | None) -> list[HistoricalEventProfile]:
        existing = self.db.query(HistoricalEventProfile).all()
        existing_event_ids = {
            profile.event_id for profile in existing if profile.event_id is not None
        }
        events_query = self.db.query(NewsEvent)
        if exclude_event_id is not None:
            events_query = events_query.filter(NewsEvent.id != exclude_event_id)
        for event in events_query.all():
            if event.id not in existing_event_ids:
                existing.append(self._ensure_profile_for_event(event))
                existing_event_ids.add(event.id)
        return [
            profile
            for profile in existing
            if exclude_event_id is None or profile.event_id != exclude_event_id
        ]

    def _ensure_profile_for_event(self, event: NewsEvent) -> HistoricalEventProfile:
        profile = (
            self.db.query(HistoricalEventProfile)
            .filter(HistoricalEventProfile.event_id == event.id)
            .first()
        )
        if profile is not None:
            return profile
        profile = self.profile_builder.build_from_news_event(event)
        self.db.add(profile)
        self.db.flush()
        return profile

    def _rank_profiles(
        self,
        reference: HistoricalEventProfile,
        candidates: Iterable[HistoricalEventProfile],
        limit: int,
        persist_results: bool,
    ) -> list[dict[str, object]]:
        scored: list[dict[str, object]] = []
        for candidate in candidates:
            if reference.event_id is not None and candidate.event_id == reference.event_id:
                continue
            components = self._score_components(reference, candidate)
            explanation = self._build_explanation(reference, candidate, components)
            if persist_results and reference.event_id is not None:
                self.db.add(
                    HistoricalSimilarityResult(
                        reference_event_id=reference.event_id,
                        source_event_id=reference.event_id,
                        candidate_event_id=candidate.event_id,
                        pattern_id=self._market_pattern_id(candidate.pattern_type),
                        matched_event_id=candidate.event_id,
                        reference_article_id=reference.article_id,
                        matched_article_id=candidate.article_id,
                        similarity_score=components.final_score,
                        narrative_similarity=components.narrative_similarity,
                        sentiment_similarity=components.sentiment_similarity,
                        impact_similarity=components.impact_similarity,
                        price_behavior_similarity=components.price_behavior_similarity,
                        reaction_similarity_score=components.price_behavior_similarity,
                        confidence_similarity=components.confidence_similarity,
                        time_window_similarity=components.time_window_similarity,
                        pattern_type=candidate.pattern_type,
                        reaction_15m_pct=candidate.price_change_15m_pct,
                        reaction_1h_pct=candidate.price_change_1h_pct,
                        reaction_4h_pct=candidate.price_change_4h_pct,
                        reaction_24h_pct=candidate.price_change_24h_pct,
                        reaction_direction=self._reaction_direction(candidate),
                        confidence_score=components.confidence_similarity,
                        explanation_json=explanation,
                        limitations_json={"limitations": explanation.get("limitations", [])},
                    )
                )
                pattern_id = self._market_pattern_id(candidate.pattern_type)
                if pattern_id is not None and candidate.event_id is not None:
                    raw_reasons = explanation.get("reasons", [])
                    reason_items = raw_reasons if isinstance(raw_reasons, list) else []
                    occurrence = PatternOccurrence(
                        pattern_id=pattern_id,
                        event_id=candidate.event_id,
                        article_id=candidate.article_id,
                        occurred_at=candidate.created_at,
                        confidence_score=components.final_score,
                        classification_reason="; ".join(str(item) for item in reason_items),
                    )
                    self.db.add(occurrence)
                    self.db.flush()
                    PATTERN_OCCURRENCES_TOTAL.inc()
                    self.db.add(
                        PatternReactionSnapshot(
                            pattern_id=pattern_id,
                            occurrence_id=occurrence.id,
                            event_id=candidate.event_id,
                            reaction_window=self._dominant_window(candidate) or "4h",
                            move_pct=candidate.price_change_4h_pct,
                            direction=self._reaction_direction(candidate),
                            provider_confidence=candidate.provider_confidence,
                            reaction_json=self._moves(candidate),
                        )
                    )
                if candidate.event_id is not None:
                    direction_match = (
                        1.0
                        if self._reaction_direction(reference)
                        == self._reaction_direction(candidate)
                        else 0.0
                    )
                    self.db.add(
                        HistoricalSimilarityMatch(
                            event_id=reference.event_id,
                            similar_event_id=candidate.event_id,
                            similarity_score=components.final_score,
                            pattern_match_score=components.event_type_match,
                            sentiment_match_score=components.sentiment_similarity,
                            market_context_match_score=components.impact_similarity,
                            time_distance_days=0.0,
                            reaction_similarity_score=components.price_behavior_similarity,
                            confidence_score=components.confidence_similarity,
                            time_structure_score=components.time_window_similarity,
                            sentiment_match=components.sentiment_similarity,
                            direction_match=direction_match,
                            provider_confidence=candidate.provider_confidence,
                            overall_confidence=components.final_score,
                            explanation_json=explanation,
                        )
                    )
                self.db.add(
                    HistoricalSimilarityRecord(
                        reference_event_id=reference.event_id,
                        reference_article_id=reference.article_id,
                        candidate_event_id=candidate.event_id,
                        candidate_article_id=candidate.article_id,
                        similarity_score=components.final_score,
                        event_type_match=components.event_type_match,
                        sentiment_match=components.sentiment_similarity,
                        impact_match=components.impact_similarity,
                        narrative_match=components.narrative_similarity,
                        reaction_match=components.price_behavior_similarity,
                        reaction_15m_pct=candidate.price_change_15m_pct,
                        reaction_1h_pct=candidate.price_change_1h_pct,
                        reaction_4h_pct=candidate.price_change_4h_pct,
                        reaction_24h_pct=candidate.price_change_24h_pct,
                        confidence_score=components.confidence_similarity,
                        explanation_json=explanation,
                    )
                )
            scored.append(self._payload(candidate, components, explanation))
        if persist_results and scored:
            self.db.flush()
        scored.sort(
            key=lambda row: (
                -self._sort_float(row.get("similarity_score")),
                self._sort_int(row.get("event_id")),
            )
        )
        return scored[: max(0, min(limit, 50))]

    def _score_components(
        self, reference: HistoricalEventProfile, candidate: HistoricalEventProfile
    ) -> SimilarityComponents:
        return SimilarityComponents(
            event_type_match=self._event_type_similarity(reference, candidate),
            narrative_similarity=self._narrative_similarity(reference, candidate),
            sentiment_similarity=self._sentiment_similarity(
                reference.sentiment_label, candidate.sentiment_label
            ),
            impact_similarity=self._impact_similarity(reference, candidate),
            price_behavior_similarity=self._price_behavior_similarity(reference, candidate),
            confidence_similarity=self._confidence_similarity(reference, candidate),
            time_window_similarity=self._time_window_similarity(reference, candidate),
        )

    def _event_type_similarity(
        self, reference: HistoricalEventProfile, candidate: HistoricalEventProfile
    ) -> float:
        if self._norm(reference.event_type) == self._norm(candidate.event_type):
            return 1.0
        if self._norm(reference.pattern_type) == self._norm(candidate.pattern_type):
            return 0.75
        return 0.2

    def _narrative_similarity(
        self, reference: HistoricalEventProfile, candidate: HistoricalEventProfile
    ) -> float:
        if reference.pattern_type == candidate.pattern_type and reference.pattern_type != "UNKNOWN":
            return 1.0
        if self._norm(reference.primary_narrative) == self._norm(candidate.primary_narrative):
            return 0.75
        if self._norm(reference.event_type) == self._norm(candidate.event_type):
            return 0.55
        return 0.2

    def _sentiment_similarity(self, reference: str | None, candidate: str | None) -> float:
        ref = self._norm(reference)
        cand = self._norm(candidate)
        if not ref or not cand or "unknown" in {ref, cand}:
            return 0.5
        if ref == cand:
            return 1.0
        if "neutral" in {ref, cand}:
            return 0.55
        return 0.15

    def _impact_similarity(
        self, reference: HistoricalEventProfile, candidate: HistoricalEventProfile
    ) -> float:
        pairs = [
            (reference.btc_relevance_score, candidate.btc_relevance_score),
            (reference.market_impact_score, candidate.market_impact_score),
            (reference.institutional_score, candidate.institutional_score),
            (reference.macro_score, candidate.macro_score),
            (reference.security_score, candidate.security_score),
            (reference.regulatory_score, candidate.regulatory_score),
            (reference.sovereignty_score, candidate.sovereignty_score),
        ]
        return self._average(1.0 - min(abs((a or 0.0) - (b or 0.0)), 1.0) for a, b in pairs)

    def _price_behavior_similarity(
        self, reference: HistoricalEventProfile, candidate: HistoricalEventProfile
    ) -> float:
        reference_moves = self._moves(reference)
        candidate_moves = self._moves(candidate)
        scores = []
        for window, reference_value in reference_moves.items():
            candidate_value = candidate_moves[window]
            if reference_value is None or candidate_value is None:
                continue
            scores.append(1.0 - min(abs(reference_value - candidate_value) / 5.0, 1.0))
        return self._average(scores, default=0.5)

    def _confidence_similarity(
        self, reference: HistoricalEventProfile, candidate: HistoricalEventProfile
    ) -> float:
        return self._average(
            [
                1.0 - min(abs(reference.confidence_score - candidate.confidence_score), 1.0),
                1.0 - min(abs(reference.provider_confidence - candidate.provider_confidence), 1.0),
            ]
        )

    def _time_window_similarity(
        self, reference: HistoricalEventProfile, candidate: HistoricalEventProfile
    ) -> float:
        ref_window = self._dominant_window(reference)
        cand_window = self._dominant_window(candidate)
        if ref_window is None or cand_window is None:
            return 0.5
        if ref_window == cand_window:
            return 1.0
        order = ["15m", "1h", "4h", "24h"]
        distance = abs(order.index(ref_window) - order.index(cand_window))
        return {1: 0.65, 2: 0.4}.get(distance, 0.25)

    def _build_explanation(
        self,
        reference: HistoricalEventProfile,
        candidate: HistoricalEventProfile,
        components: SimilarityComponents,
    ) -> dict[str, object]:
        reasons: list[str] = []
        if reference.pattern_type == candidate.pattern_type and reference.pattern_type != "UNKNOWN":
            reasons.append(f"same pattern type: {reference.pattern_type}")
        if self._norm(reference.primary_narrative) == self._norm(candidate.primary_narrative):
            reasons.append(f"same narrative: {reference.primary_narrative}")
        if self._sentiment_similarity(reference.sentiment_label, candidate.sentiment_label) >= 0.9:
            reasons.append(f"same {self._norm(reference.sentiment_label)} sentiment")
        dominant = self._dominant_window(reference)
        if dominant and dominant == self._dominant_window(candidate):
            reasons.append(f"similar dominant reaction window: {dominant}")
        if components.price_behavior_similarity >= 0.75:
            reasons.append("similar BTC price reaction profile")
        if components.confidence_similarity >= 0.75:
            reasons.append("similar confidence and provider-confidence profile")
        if not reasons:
            reasons.append("partial overlap across narrative and market-reaction features")
        return {
            "similarity_score": components.final_score,
            "reasons": reasons,
            "limitations": self._limitations(
                [
                    CORRELATION_LIMITATION,
                    PAST_PERFORMANCE_LIMITATION,
                    "Market conditions differ across historical windows.",
                ]
            ),
            "components": {
                "event_type_match": components.event_type_match,
                "narrative_similarity": components.narrative_similarity,
                "sentiment_similarity": components.sentiment_similarity,
                "impact_similarity": components.impact_similarity,
                "price_behavior_similarity": components.price_behavior_similarity,
                "confidence_similarity": components.confidence_similarity,
                "time_window_similarity": components.time_window_similarity,
            },
        }

    def _payload(
        self,
        candidate: HistoricalEventProfile,
        components: SimilarityComponents,
        explanation: dict[str, object],
    ) -> dict[str, object]:
        return {
            "event_id": candidate.event_id,
            "article_id": candidate.article_id,
            "title": candidate.canonical_title,
            "pattern_type": candidate.pattern_type,
            "date": candidate.created_at,
            "similarity_score": components.final_score,
            "reaction_15m": candidate.price_change_15m_pct,
            "reaction_1h": candidate.price_change_1h_pct,
            "reaction_4h": candidate.price_change_4h_pct,
            "reaction_24h": candidate.price_change_24h_pct,
            "confidence": candidate.confidence_score,
            "matched_pattern": candidate.pattern_type,
            "btc_reaction_after_4h": candidate.price_change_4h_pct,
            "confidence_breakdown": explanation.get("components", {}),
            "limitations": explanation.get("limitations", []),
            "summary": self._result_summary(candidate, explanation),
            "explanation": explanation,
        }

    def _result_summary(
        self, candidate: HistoricalEventProfile, explanation: dict[str, object]
    ) -> str:
        reasons = explanation.get("reasons", [])
        lead = f"Historically similar {candidate.pattern_type} event"
        if reasons and isinstance(reasons, list):
            return f"{lead}: {reasons[0]}."
        return f"{lead} identified with correlation-only evidence."

    def _summary(self, similar_events: list[dict[str, object]]) -> str:
        if not similar_events:
            return "No sufficiently similar historical events were identified."
        top = similar_events[0]
        return (
            f"Top historical comparison: {top.get('pattern_type')} at "
            f"similarity {top.get('similarity_score')}. Historical reactions are context, not predictions."
        )

    def _report_for_event(
        self,
        event: NewsEvent,
        similar_events: list[dict[str, object]],
        classifications: list[dict[str, object]],
    ) -> HistoricalSimilarityReport:
        reactions = self._reaction_statistics(similar_events)
        confidence = self._report_confidence(similar_events)
        return HistoricalSimilarityReport(
            reference_event={
                "event_id": event.id,
                "article_id": event.primary_article_id,
                "title": event.canonical_title,
                "event_type": event.event_type,
                "sentiment": event.event_sentiment,
                "provider_confidence": event.provider_confidence,
            },
            similar_events=similar_events,
            similarity_band=self.similarity_band(confidence),
            sample_size=len(similar_events),
            median_reaction_15m=reactions["median"].get("reaction_15m"),
            median_reaction_1h=reactions["median"].get("reaction_1h"),
            median_reaction_4h=reactions["median"].get("reaction_4h"),
            median_reaction_24h=reactions["median"].get("reaction_24h"),
            average_reaction_15m=reactions["average"].get("reaction_15m"),
            average_reaction_1h=reactions["average"].get("reaction_1h"),
            average_reaction_4h=reactions["average"].get("reaction_4h"),
            average_reaction_24h=reactions["average"].get("reaction_24h"),
            confidence=confidence,
            limitations=self._limitations(
                [CORRELATION_LIMITATION, PAST_PERFORMANCE_LIMITATION, HISTORICAL_OUTCOME_LIMITATION]
            ),
            evidence={
                "pattern_classification": classifications,
                "candidate_events": similar_events,
                "reaction_statistics": reactions,
                "confidence_reasoning": self._confidence_reasoning(similar_events, confidence),
                "limitations": self._limitations(
                    [
                        CORRELATION_LIMITATION,
                        PAST_PERFORMANCE_LIMITATION,
                        HISTORICAL_OUTCOME_LIMITATION,
                    ]
                ),
            },
        )

    def _empty_report(self, reference: dict[str, object]) -> HistoricalSimilarityReport:
        return HistoricalSimilarityReport(
            reference_event=reference,
            similar_events=[],
            similarity_band="Weak",
            sample_size=0,
            confidence=0.0,
            limitations=self._limitations(
                [CORRELATION_LIMITATION, PAST_PERFORMANCE_LIMITATION, HISTORICAL_OUTCOME_LIMITATION]
            ),
            evidence={
                "pattern_classification": [],
                "candidate_events": [],
                "reaction_statistics": {},
                "confidence_reasoning": ["No historical analogs available for this reference."],
                "limitations": self._limitations(
                    [
                        CORRELATION_LIMITATION,
                        PAST_PERFORMANCE_LIMITATION,
                        HISTORICAL_OUTCOME_LIMITATION,
                    ]
                ),
            },
        )

    def _reaction_statistics(
        self, similar_events: list[dict[str, object]]
    ) -> dict[str, dict[str, float | None]]:
        windows = ["reaction_15m", "reaction_1h", "reaction_4h", "reaction_24h"]
        stats: dict[str, dict[str, float | None]] = {"median": {}, "average": {}, "dispersion": {}}
        for window in windows:
            values = []
            for row in similar_events:
                value = row.get(window)
                if isinstance(value, (int, float)):
                    values.append(float(value))
            stats["median"][window] = round(median(values), 6) if values else None
            stats["average"][window] = round(mean(values), 6) if values else None
            stats["dispersion"][window] = (
                round(max(values) - min(values), 6) if len(values) > 1 else 0.0 if values else None
            )
        return stats

    def _report_confidence(self, similar_events: list[dict[str, object]]) -> float:
        if not similar_events:
            return 0.0
        similarity_values = []
        for row in similar_events:
            value = row.get("similarity_score")
            if isinstance(value, (int, float)):
                similarity_values.append(float(value))
        if not similarity_values:
            return 0.0
        avg_similarity = mean(similarity_values)
        sample_weight = min(1.0, len(similar_events) / 5.0)
        return round(max(0.0, min(1.0, avg_similarity * (0.65 + 0.35 * sample_weight))), 6)

    def _confidence_reasoning(
        self, similar_events: list[dict[str, object]], confidence: float
    ) -> list[str]:
        return [
            f"sample_size={len(similar_events)}",
            f"confidence={confidence}",
            "confidence is reduced for small samples and remains informational only",
        ]

    def _limitations(self, existing: list[str]) -> list[str]:
        output = list(existing)
        for item in REQUIRED_LIMITATIONS:
            if item not in output:
                output.append(item)
        return output

    def _band_label(self, value: float) -> str:
        if value >= 0.90:
            return "VERY_HIGH"
        if value >= 0.75:
            return "HIGH"
        if value >= 0.60:
            return "MEDIUM"
        if value >= 0.40:
            return "LOW"
        return "VERY_LOW"

    def _market_pattern_id(self, pattern_type: object) -> int | None:
        if not pattern_type:
            return None
        slug = str(pattern_type).upper()
        row = self.db.query(MarketPatternModel).filter(MarketPatternModel.slug == slug).first()
        if row is None:
            MarketMemoryService(self.db).ensure_patterns()
            row = self.db.query(MarketPatternModel).filter(MarketPatternModel.slug == slug).first()
        return row.id if row is not None else None

    def _pattern_category(self, pattern_type: object) -> str | None:
        if not pattern_type:
            return None
        row = (
            self.db.query(MarketPatternModel)
            .filter(MarketPatternModel.slug == str(pattern_type).upper())
            .first()
        )
        return row.category if row is not None else None

    def _median_or_none(self, values: list[float]) -> float | None:
        return round(float(median(values)), 6) if values else None

    def _reaction_statistics_payload(self, row: HistoricalReactionStatistics) -> dict[str, object]:
        return {
            "id": row.id,
            "pattern_id": row.pattern_id,
            "samples": row.samples,
            "median_move_15m": row.median_move_15m,
            "median_move_1h": row.median_move_1h,
            "median_move_4h": row.median_move_4h,
            "median_move_24h": row.median_move_24h,
            "positive_ratio": row.positive_ratio,
            "negative_ratio": row.negative_ratio,
            "neutral_ratio": row.neutral_ratio,
            "updated_at": row.updated_at,
        }

    def _narrative_tags(self, reference_event: dict[str, object]) -> list[str]:
        text = f"{reference_event.get('title', '')} {reference_event.get('event_type', '')}".lower()
        tags = []
        for tag in [
            "ETF",
            "Macro",
            "Mining",
            "Lightning",
            "Bitcoin Core",
            "Institutional Adoption",
            "Self Custody",
            "Security",
            "Regulation",
            "Liquidity",
        ]:
            if tag.lower().split()[0] in text:
                tags.append(tag)
        return tags or [str(reference_event.get("event_type", "unknown"))]

    def similarity_band(self, value: float) -> str:
        if value < 0.40:
            return "Weak"
        if value < 0.60:
            return "Moderate"
        if value < 0.80:
            return "Strong"
        return "Very Strong"

    def _reaction_direction(self, profile: HistoricalEventProfile) -> str:
        values = [
            profile.price_change_15m_pct,
            profile.price_change_1h_pct,
            profile.price_change_4h_pct,
            profile.price_change_24h_pct,
        ]
        strongest = max(
            (float(value) for value in values if value is not None), key=abs, default=0.0
        )
        if strongest > 0:
            return "UP"
        if strongest < 0:
            return "DOWN"
        return "FLAT"

    def _moves(self, profile: HistoricalEventProfile) -> dict[str, float | None]:
        return {
            "15m": profile.price_change_15m_pct,
            "1h": profile.price_change_1h_pct,
            "4h": profile.price_change_4h_pct,
            "24h": profile.price_change_24h_pct,
        }

    def _dominant_window(self, profile: HistoricalEventProfile) -> str | None:
        moves = {
            window: value for window, value in self._moves(profile).items() if value is not None
        }
        if not moves:
            return None
        return max(moves, key=lambda window: abs(moves[window] or 0.0))

    def _sort_float(self, value: object) -> float:
        if isinstance(value, (float, int)):
            return float(value)
        return 0.0

    def _sort_int(self, value: object) -> int:
        if isinstance(value, int):
            return value
        return 0

    def _average(self, values: Iterable[float], default: float = 0.0) -> float:
        numbers = list(values)
        if not numbers:
            return default
        return round(sum(numbers) / len(numbers), 6)

    def _norm(self, value: str | None) -> str:
        return (value or "").strip().lower()
