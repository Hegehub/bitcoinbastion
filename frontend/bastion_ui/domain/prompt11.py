# mypy: disable-error-code="attr-defined"
"""Feature-54 projection for backend-authoritative Market similarity."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from bastion_ui.transport.generated_http import MarketSimilarityReportSuccess


class FrozenViewModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class SimilarityDimensionViewModel(FrozenViewModel):
    name: str
    score_ratio: Decimal


class SimilarityMatchViewModel(FrozenViewModel):
    rank: int
    candidate_event_id: int
    candidate_title: str
    candidate_occurred_at: datetime
    replay_event_id: int
    score_ratio: Decimal
    score_meaning: str
    dimensions: tuple[SimilarityDimensionViewModel, ...]
    limitations: tuple[str, ...]


class StatisticalIntervalViewModel(FrozenViewModel):
    subject: str
    lower: Decimal
    upper: Decimal
    unit: str
    interval_type: str
    lower_quantile: Decimal
    upper_quantile: Decimal
    method_id: str
    method_version: str
    sample_count: int
    cohort: str
    limitations: tuple[str, ...]


class SimilarityReportViewModel(FrozenViewModel):
    reference_event_id: int
    method: str
    method_version: str
    interpretation: str
    results: tuple[SimilarityMatchViewModel, ...]
    sufficiency: str
    sample_count: int
    coverage_dimension_count: int
    confidence_ratio: Decimal | None
    uncertainty_limitations: tuple[str, ...]
    interval: StatisticalIntervalViewModel | None


def adapt_similarity(response: MarketSimilarityReportSuccess) -> SimilarityReportViewModel:
    report = response.root
    interval = report.uncertainty.interval
    return SimilarityReportViewModel(
        reference_event_id=report.reference_event_id,
        method=report.method.root if report.method is not None else "WEIGHTED_EVENT_CONTEXT_V1",
        method_version=report.method_version or "historical-event-similarity.v1",
        interpretation=report.interpretation or "RETROSPECTIVE_COMPARISON_NOT_FORECAST",
        results=tuple(
            SimilarityMatchViewModel(
                rank=item.rank,
                candidate_event_id=item.candidate_event_id,
                candidate_title=item.candidate_title,
                candidate_occurred_at=item.candidate_occurred_at,
                replay_event_id=item.replay_event_id,
                score_ratio=item.score_ratio,
                score_meaning=item.score_meaning
                or "HIGHER_IS_MORE_SIMILAR_NOT_PREDICTIVE",
                dimensions=tuple(
                    SimilarityDimensionViewModel(
                        name=dimension.dimension, score_ratio=dimension.score_ratio
                    )
                    for dimension in item.dimensions
                ),
                limitations=tuple(item.limitations),
            )
            for item in report.results
        ),
        sufficiency=report.uncertainty.sufficiency.root,
        sample_count=report.uncertainty.sample_count,
        coverage_dimension_count=report.uncertainty.coverage_dimension_count,
        confidence_ratio=report.uncertainty.confidence_ratio,
        uncertainty_limitations=tuple(report.uncertainty.limitations or ()),
        interval=None
        if interval is None
        else StatisticalIntervalViewModel(
            subject=interval.subject.root,
            lower=interval.lower,
            upper=interval.upper,
            unit=interval.unit or "SIMILARITY_RATIO",
            interval_type=interval.interval_type.root,
            lower_quantile=interval.lower_quantile,
            upper_quantile=interval.upper_quantile,
            method_id=interval.method_id,
            method_version=interval.method_version,
            sample_count=interval.sample_count,
            cohort=interval.cohort,
            limitations=tuple(interval.limitations),
        ),
    )
