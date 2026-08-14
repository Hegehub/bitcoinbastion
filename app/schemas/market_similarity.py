"""Strict analytical contracts for historical Market similarity.

Similarity is retrospective comparison, never a forecast.  The contract deliberately
does not contain future-return or outcome-probability fields.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictSimilarityModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class SimilarityMethod(StrEnum):
    WEIGHTED_EVENT_CONTEXT_V1 = "WEIGHTED_EVENT_CONTEXT_V1"


class DataSufficiency(StrEnum):
    AVAILABLE = "AVAILABLE"
    INSUFFICIENT = "INSUFFICIENT"


class SimilarityDimensionOut(StrictSimilarityModel):
    dimension: Literal["PATTERN", "SENTIMENT", "IMPACT", "VOLATILITY"]
    score_ratio: float = Field(ge=0, le=1)


class SimilarityUncertaintyOut(StrictSimilarityModel):
    """Non-statistical support metadata; it is not a probability or interval."""

    sufficiency: DataSufficiency
    sample_count: int = Field(ge=0)
    coverage_dimension_count: int = Field(ge=0, le=4)
    confidence_ratio: float | None = Field(default=None, ge=0, le=1)
    limitations: tuple[str, ...] = ()
    interval: SimilarityStatisticalIntervalOut | None = None


class SimilarityIntervalType(StrEnum):
    EMPIRICAL_QUANTILE_INTERVAL = "EMPIRICAL_QUANTILE_INTERVAL"


class SimilarityIntervalSubject(StrEnum):
    HISTORICAL_CANDIDATE_SIMILARITY_SCORE_DISTRIBUTION = (
        "HISTORICAL_CANDIDATE_SIMILARITY_SCORE_DISTRIBUTION"
    )


class SimilarityStatisticalIntervalOut(StrictSimilarityModel):
    subject: SimilarityIntervalSubject
    lower: float = Field(ge=0, le=1)
    upper: float = Field(ge=0, le=1)
    unit: Literal["SIMILARITY_RATIO"] = "SIMILARITY_RATIO"
    interval_type: SimilarityIntervalType
    lower_quantile: float = Field(ge=0, le=1)
    upper_quantile: float = Field(ge=0, le=1)
    method_id: Literal["EMPIRICAL_SIMILARITY_SCORE_QUANTILES"]
    method_version: Literal["empirical-similarity-quantiles.v1"]
    sample_count: int = Field(ge=5)
    cohort: Literal["ELIGIBLE_PERSISTED_MATCHES_BOUNDED_500_AT_REQUEST_BOUNDARY"]
    limitations: tuple[str, ...]

    @model_validator(mode="after")
    def valid_bounds(self) -> SimilarityStatisticalIntervalOut:
        if self.lower > self.upper:
            raise ValueError("interval lower must not exceed upper")
        if self.lower_quantile >= self.upper_quantile:
            raise ValueError("lower quantile must be below upper quantile")
        return self


class MarketSimilarityMatchOut(StrictSimilarityModel):
    result_id: int
    rank: int = Field(ge=1)
    reference_event_id: int
    candidate_event_id: int
    candidate_title: str
    candidate_occurred_at: datetime
    replay_event_id: int
    score_ratio: float = Field(ge=0, le=1)
    score_meaning: Literal["HIGHER_IS_MORE_SIMILAR_NOT_PREDICTIVE"] = (
        "HIGHER_IS_MORE_SIMILAR_NOT_PREDICTIVE"
    )
    method: SimilarityMethod = SimilarityMethod.WEIGHTED_EVENT_CONTEXT_V1
    method_version: Literal["historical-event-similarity.v1"] = (
        "historical-event-similarity.v1"
    )
    dimensions: tuple[SimilarityDimensionOut, ...]
    limitations: tuple[str, ...]


class MarketSimilarityReportOut(StrictSimilarityModel):
    reference_event_id: int
    method: SimilarityMethod = SimilarityMethod.WEIGHTED_EVENT_CONTEXT_V1
    method_version: Literal["historical-event-similarity.v1"] = (
        "historical-event-similarity.v1"
    )
    results: tuple[MarketSimilarityMatchOut, ...]
    uncertainty: SimilarityUncertaintyOut
    generated_at: datetime
    provenance: Literal["LIVE"] = "LIVE"
    interpretation: Literal["RETROSPECTIVE_COMPARISON_NOT_FORECAST"] = (
        "RETROSPECTIVE_COMPARISON_NOT_FORECAST"
    )

    @model_validator(mode="after")
    def ranks_are_canonical(self) -> MarketSimilarityReportOut:
        if tuple(item.rank for item in self.results) != tuple(range(1, len(self.results) + 1)):
            raise ValueError("similarity results must use contiguous backend ranks")
        return self
