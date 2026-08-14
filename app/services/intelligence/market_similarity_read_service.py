"""Typed read projection over persisted historical similarity authority."""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy.orm import Session

from app.db.models.historical_event_similarity import HistoricalEventSimilarity
from app.db.models.news_event import NewsEvent
from app.db.models.time_utils import utcnow
from app.domain.market_similarity_interval import (
    EmpiricalSimilarityIntervalMethod,
    IntervalSufficiency,
    SimilarityScoreObservation,
)
from app.schemas.market_similarity import (
    DataSufficiency,
    MarketSimilarityMatchOut,
    MarketSimilarityReportOut,
    SimilarityDimensionOut,
    SimilarityIntervalSubject,
    SimilarityIntervalType,
    SimilarityStatisticalIntervalOut,
    SimilarityUncertaintyOut,
)

NOT_PREDICTION = "Historical similarity is retrospective and does not predict future outcomes."
NO_CAUSALITY = "Similarity and temporal association are not proof of causation."


class MarketSimilarityReadService:
    """Preserve the engine's persisted scores and deterministic backend ordering."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def report(self, reference_event_id: int, *, limit: int = 10) -> MarketSimilarityReportOut:
        cohort_rows = (
            self.db.query(HistoricalEventSimilarity, NewsEvent)
            .join(NewsEvent, NewsEvent.id == HistoricalEventSimilarity.similar_event_id)
            .filter(HistoricalEventSimilarity.event_id == reference_event_id)
            .order_by(
                HistoricalEventSimilarity.similarity_score.desc(),
                NewsEvent.first_seen_at.desc(),
                HistoricalEventSimilarity.id.asc(),
            )
            .limit(500)
            .all()
        )
        rows = cohort_rows[:limit]
        matches = tuple(self._match(row, event, rank) for rank, (row, event) in enumerate(rows, 1))
        count = len(cohort_rows)
        empirical = EmpiricalSimilarityIntervalMethod().calculate(
            tuple(
                SimilarityScoreObservation(
                    candidate_event_id=row.similar_event_id,
                    score_ratio=Decimal(str(row.similarity_score)),
                )
                for row, _ in cohort_rows
            )
        )
        interval = None
        if empirical.sufficiency is IntervalSufficiency.AVAILABLE:
            assert empirical.lower is not None and empirical.upper is not None
            interval = SimilarityStatisticalIntervalOut(
                subject=SimilarityIntervalSubject.HISTORICAL_CANDIDATE_SIMILARITY_SCORE_DISTRIBUTION,
                lower=float(empirical.lower),
                upper=float(empirical.upper),
                interval_type=SimilarityIntervalType.EMPIRICAL_QUANTILE_INTERVAL,
                lower_quantile=float(empirical.lower_quantile),
                upper_quantile=float(empirical.upper_quantile),
                method_id=EmpiricalSimilarityIntervalMethod.method_id,
                method_version=EmpiricalSimilarityIntervalMethod.method_version,
                sample_count=empirical.sample_count,
                cohort="ELIGIBLE_PERSISTED_MATCHES_BOUNDED_500_AT_REQUEST_BOUNDARY",
                limitations=tuple(item.value for item in empirical.limitations),
            )
        sufficiency = DataSufficiency.AVAILABLE if count else DataSufficiency.INSUFFICIENT
        limitations = [NOT_PREDICTION, NO_CAUSALITY]
        if not count:
            limitations.append("No persisted historical comparisons are available.")
        return MarketSimilarityReportOut(
            reference_event_id=reference_event_id,
            results=matches,
            uncertainty=SimilarityUncertaintyOut(
                sufficiency=sufficiency,
                sample_count=count,
                coverage_dimension_count=4 if count else 0,
                confidence_ratio=None,
                limitations=tuple(limitations),
                interval=interval,
            ),
            generated_at=utcnow(),
        )

    @staticmethod
    def _match(
        row: HistoricalEventSimilarity, event: NewsEvent, rank: int
    ) -> MarketSimilarityMatchOut:
        return MarketSimilarityMatchOut(
            result_id=row.id,
            rank=rank,
            reference_event_id=row.event_id,
            candidate_event_id=row.similar_event_id,
            candidate_title=event.canonical_title,
            candidate_occurred_at=event.first_seen_at,
            replay_event_id=row.similar_event_id,
            score_ratio=row.similarity_score,
            dimensions=(
                SimilarityDimensionOut(
                    dimension="PATTERN", score_ratio=1.0 if row.pattern_match else 0.0
                ),
                SimilarityDimensionOut(dimension="SENTIMENT", score_ratio=row.sentiment_match),
                SimilarityDimensionOut(dimension="IMPACT", score_ratio=row.impact_match),
                SimilarityDimensionOut(
                    dimension="VOLATILITY", score_ratio=row.volatility_match
                ),
            ),
            limitations=(NOT_PREDICTION, NO_CAUSALITY),
        )
