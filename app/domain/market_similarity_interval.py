"""Feature-20 empirical dispersion authority for historical similarity scores.

This module describes a retrospective empirical cohort.  It does not estimate a
population parameter and does not predict a future Market outcome.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
from math import isfinite


class IntervalSufficiency(StrEnum):
    AVAILABLE = "AVAILABLE"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


class IntervalLimitation(StrEnum):
    DESCRIPTIVE_NOT_CONFIDENCE_INTERVAL = "DESCRIPTIVE_NOT_CONFIDENCE_INTERVAL"
    TEMPORAL_DEPENDENCE_NOT_MODELED = "TEMPORAL_DEPENDENCE_NOT_MODELED"
    RETROSPECTIVE_NOT_FORECAST = "RETROSPECTIVE_NOT_FORECAST"
    LOW_SAMPLE_COUNT = "LOW_SAMPLE_COUNT"


@dataclass(frozen=True, slots=True)
class SimilarityScoreObservation:
    """One eligible historical candidate context and its persisted score."""

    candidate_event_id: int
    score_ratio: Decimal

    def __post_init__(self) -> None:
        if self.candidate_event_id <= 0:
            raise ValueError("candidate event identity must be positive")
        if not self.score_ratio.is_finite() or not Decimal("0") <= self.score_ratio <= Decimal("1"):
            raise ValueError("similarity score must be finite and within [0, 1]")


@dataclass(frozen=True, slots=True)
class EmpiricalSimilarityInterval:
    lower: Decimal | None
    upper: Decimal | None
    lower_quantile: Decimal
    upper_quantile: Decimal
    sample_count: int
    sufficiency: IntervalSufficiency
    limitations: tuple[IntervalLimitation, ...]


class EmpiricalSimilarityIntervalMethod:
    """Hyndman-Fan type-7 empirical quantiles over distinct candidate contexts."""

    method_id = "EMPIRICAL_SIMILARITY_SCORE_QUANTILES"
    method_version = "empirical-similarity-quantiles.v1"
    lower_quantile = Decimal("0.10")
    upper_quantile = Decimal("0.90")
    minimum_sample_count = 5

    def calculate(
        self, observations: tuple[SimilarityScoreObservation, ...]
    ) -> EmpiricalSimilarityInterval:
        identities = [item.candidate_event_id for item in observations]
        if len(identities) != len(set(identities)):
            raise ValueError("candidate contexts must be unique sampling units")
        common = (
            IntervalLimitation.DESCRIPTIVE_NOT_CONFIDENCE_INTERVAL,
            IntervalLimitation.TEMPORAL_DEPENDENCE_NOT_MODELED,
            IntervalLimitation.RETROSPECTIVE_NOT_FORECAST,
        )
        if len(observations) < self.minimum_sample_count:
            return EmpiricalSimilarityInterval(
                lower=None,
                upper=None,
                lower_quantile=self.lower_quantile,
                upper_quantile=self.upper_quantile,
                sample_count=len(observations),
                sufficiency=IntervalSufficiency.INSUFFICIENT_DATA,
                limitations=common + (IntervalLimitation.LOW_SAMPLE_COUNT,),
            )
        values = tuple(sorted(item.score_ratio for item in observations))
        return EmpiricalSimilarityInterval(
            lower=self._type7(values, self.lower_quantile),
            upper=self._type7(values, self.upper_quantile),
            lower_quantile=self.lower_quantile,
            upper_quantile=self.upper_quantile,
            sample_count=len(values),
            sufficiency=IntervalSufficiency.AVAILABLE,
            limitations=common,
        )

    @staticmethod
    def _type7(values: tuple[Decimal, ...], quantile: Decimal) -> Decimal:
        if not values or not quantile.is_finite() or not Decimal("0") <= quantile <= Decimal("1"):
            raise ValueError("type-7 quantile requires finite values and quantile in [0, 1]")
        position = Decimal(len(values) - 1) * quantile
        lower_index = int(position)
        fraction = position - Decimal(lower_index)
        upper_index = min(lower_index + 1, len(values) - 1)
        result = values[lower_index] + fraction * (values[upper_index] - values[lower_index])
        if not isfinite(float(result)):
            raise ValueError("empirical interval result must be finite")
        return result.quantize(Decimal("0.000001"))
