from decimal import Decimal

import pytest

from app.domain.market_similarity_interval import (
    EmpiricalSimilarityIntervalMethod,
    IntervalLimitation,
    IntervalSufficiency,
    SimilarityScoreObservation,
)


def _observations(*values: str) -> tuple[SimilarityScoreObservation, ...]:
    return tuple(
        SimilarityScoreObservation(candidate_event_id=index, score_ratio=Decimal(value))
        for index, value in enumerate(values, 1)
    )


def test_type7_empirical_quantiles_known_sample() -> None:
    result = EmpiricalSimilarityIntervalMethod().calculate(
        _observations("0.5", "0.6", "0.7", "0.8", "0.875")
    )
    assert result.lower == Decimal("0.540000")
    assert result.upper == Decimal("0.845000")
    assert result.sufficiency is IntervalSufficiency.AVAILABLE
    assert result.sample_count == 5
    assert IntervalLimitation.DESCRIPTIVE_NOT_CONFIDENCE_INTERVAL in result.limitations
    assert IntervalLimitation.RETROSPECTIVE_NOT_FORECAST in result.limitations


def test_minimum_sample_is_five_and_never_returns_fake_bounds() -> None:
    insufficient = EmpiricalSimilarityIntervalMethod().calculate(
        _observations("0", "0.2", "0.4", "1")
    )
    assert insufficient.sufficiency is IntervalSufficiency.INSUFFICIENT_DATA
    assert insufficient.lower is None and insufficient.upper is None
    assert IntervalLimitation.LOW_SAMPLE_COUNT in insufficient.limitations


def test_constant_and_zero_samples_are_valid() -> None:
    constant = EmpiricalSimilarityIntervalMethod().calculate(
        _observations("0", "0", "0", "0", "0")
    )
    assert constant.lower == constant.upper == Decimal("0.000000")


@pytest.mark.parametrize("value", ["NaN", "Infinity", "-0.01", "1.01"])
def test_invalid_score_is_rejected(value: str) -> None:
    with pytest.raises(ValueError, match="finite"):
        SimilarityScoreObservation(candidate_event_id=1, score_ratio=Decimal(value))


def test_duplicate_candidate_context_is_rejected() -> None:
    with pytest.raises(ValueError, match="unique"):
        EmpiricalSimilarityIntervalMethod().calculate(
            (
                SimilarityScoreObservation(1, Decimal("0.1")),
                SimilarityScoreObservation(1, Decimal("0.2")),
                *_observations("0.3", "0.4", "0.5"),
            )
        )


def test_method_is_deterministic_and_order_independent() -> None:
    method = EmpiricalSimilarityIntervalMethod()
    left = method.calculate(_observations("0.9", "0.1", "0.7", "0.3", "0.5"))
    right = method.calculate(_observations("0.1", "0.3", "0.5", "0.7", "0.9"))
    assert (left.lower, left.upper) == (right.lower, right.upper)
