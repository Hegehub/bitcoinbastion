from __future__ import annotations

from sqlalchemy.orm import Session

from app.services.intelligence.historical_similarity_metrics import (
    HISTORICAL_SIMILARITY_DURATION_SECONDS,
    HISTORICAL_SIMILARITY_REQUESTS_TOTAL,
    SIMILARITY_GENERATION_FAILURES,
)

from app.db.models.news_event import NewsEvent
from app.db.models.signal import Signal
from app.schemas.intelligence.historical_similarity import HistoricalSimilarityResponse
from app.services.intelligence.historical_similarity.pattern_matcher import (
    PatternMatch,
    PatternMatcher,
)
from app.services.intelligence.historical_similarity.similarity_explainer import SimilarityExplainer
from app.services.intelligence.historical_similarity.similarity_scoring import SimilarityScoring
from app.services.intelligence.historical_similarity_service import (
    HistoricalSimilarityService as LegacyHistoricalSimilarityService,
)


class HistoricalSimilarityService:
    """Production package facade for historical similarity reports.

    The existing flat service owns persistence/profile materialization. This facade
    provides the Prompt 28 response model, package boundaries, pattern matching,
    and UI-ready fields without breaking existing callers.
    """

    def __init__(self, db: Session) -> None:
        self.db = db
        self.legacy = LegacyHistoricalSimilarityService(db)
        self.matcher = PatternMatcher()
        self.scoring = SimilarityScoring()
        self.explainer = SimilarityExplainer()

    def find_for_event(self, event_id: int, limit: int = 10) -> HistoricalSimilarityResponse:
        HISTORICAL_SIMILARITY_REQUESTS_TOTAL.inc()
        with HISTORICAL_SIMILARITY_DURATION_SECONDS.time():
            try:
                report = self.legacy.build_event_report(event_id, limit=limit)
                event = self.db.get(NewsEvent, event_id)
                pattern_matches = self.matcher.identify(event) if event is not None else []
                return self._from_report(report, pattern_matches)
            except Exception:
                SIMILARITY_GENERATION_FAILURES.inc()
                raise

    def find_for_article(self, article_id: int, limit: int = 10) -> HistoricalSimilarityResponse:
        HISTORICAL_SIMILARITY_REQUESTS_TOTAL.inc()
        with HISTORICAL_SIMILARITY_DURATION_SECONDS.time():
            try:
                report = self.legacy.build_article_report(article_id, limit=limit)
                event_id = (
                    report.reference_event.get("event_id") if report.reference_event else None
                )
                event = self.db.get(NewsEvent, event_id) if isinstance(event_id, int) else None
                pattern_matches = self.matcher.identify(event) if event is not None else []
                return self._from_report(report, pattern_matches)
            except Exception:
                SIMILARITY_GENERATION_FAILURES.inc()
                raise

    def find_for_signal(self, signal_id: int, limit: int = 10) -> HistoricalSimilarityResponse:
        HISTORICAL_SIMILARITY_REQUESTS_TOTAL.inc()
        signal = self.db.get(Signal, signal_id)
        if signal is None:
            return HistoricalSimilarityResponse(
                current_item={"signal_id": signal_id},
                limitations=[
                    "Correlation is not proof of causation.",
                    "Historical similarity does not guarantee future outcomes.",
                ],
            )
        # Signal-to-NewsEvent matching is intentionally conservative for this foundation.
        return HistoricalSimilarityResponse(
            current_item={
                "signal_id": signal.id,
                "title": signal.title,
                "signal_type": signal.signal_type,
            },
            limitations=[
                "Correlation is not proof of causation.",
                "Historical similarity does not guarantee future outcomes.",
                "No linked historical event profile is available for this signal yet.",
            ],
        )

    def _from_report(
        self, report: object, pattern_matches: list[PatternMatch]
    ) -> HistoricalSimilarityResponse:
        similar_events = list(getattr(report, "similar_events", []))
        evidence = getattr(report, "evidence", {})
        reaction_stats = (
            evidence.get("reaction_statistics", {}) if isinstance(evidence, dict) else {}
        )
        median_reaction = {
            "15m": getattr(report, "median_reaction_15m", None),
            "1h": getattr(report, "median_reaction_1h", None),
            "4h": getattr(report, "median_reaction_4h", None),
            "24h": getattr(report, "median_reaction_24h", None),
        }
        detected = [
            {"pattern": item.pattern, "score": item.score, "explanation": item.explanation}
            for item in pattern_matches
        ]
        top_score = float(similar_events[0].get("similarity_score", 0.0)) if similar_events else 0.0
        return HistoricalSimilarityResponse(
            current_item=getattr(report, "reference_event", None),
            matched_items=similar_events,
            top_similar_events=similar_events[:10],
            pattern_detected=detected,
            pattern_name=str(detected[0]["pattern"]) if detected else None,
            pattern_category=(
                str(similar_events[0].get("pattern_type", "")) if similar_events else None
            ),
            similarity_score=top_score,
            historical_matches=similar_events,
            historical_reaction_summary={
                "sample_size": getattr(report, "sample_size", 0),
                "median_reaction": median_reaction,
                "average_reaction": {
                    "15m": getattr(report, "average_reaction_15m", None),
                    "1h": getattr(report, "average_reaction_1h", None),
                    "4h": getattr(report, "average_reaction_4h", None),
                    "24h": getattr(report, "average_reaction_24h", None),
                },
            },
            median_reaction=median_reaction,
            historical_median=median_reaction,
            historical_average={
                "15m": getattr(report, "average_reaction_15m", None),
                "1h": getattr(report, "average_reaction_1h", None),
                "4h": getattr(report, "average_reaction_4h", None),
                "24h": getattr(report, "average_reaction_24h", None),
            },
            reaction_summary=reaction_stats,
            reaction_distribution=(
                reaction_stats.get("dispersion", {}) if isinstance(reaction_stats, dict) else {}
            ),
            confidence=float(getattr(report, "confidence", 0.0)),
            pattern_confidence=float(getattr(report, "confidence", 0.0)),
            reaction_statistics=reaction_stats if isinstance(reaction_stats, dict) else {},
            sample_size=int(getattr(report, "sample_size", 0)),
            similarity_band=str(getattr(report, "similarity_band", "weak")).lower(),
            limitations=list(getattr(report, "limitations", [])),
            generated_at=getattr(report, "generated_at"),
        )
