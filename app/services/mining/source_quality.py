from __future__ import annotations

from dataclasses import dataclass

SOURCE_BASE_SCORES: dict[str, float] = {
    "official_pool_docs": 0.82,
    "pool_api": 0.78,
    "public_announcement": 0.62,
    "independent_research": 0.68,
    "manual_entry": 0.35,
    "fixture": 0.2,
    "unknown": 0.25,
}


@dataclass(frozen=True)
class SourceQualityResult:
    confidence: float
    base_score: float
    freshness_penalty: float
    fallback_penalty: float
    synthetic_penalty: float
    verification_boost: float


def calculate_source_quality_confidence(
    *,
    source_type: str,
    freshness_seconds: int | None,
    is_fallback: bool = False,
    is_synthetic: bool = False,
    is_verified: bool = False,
) -> SourceQualityResult:
    base_score = SOURCE_BASE_SCORES.get(source_type, SOURCE_BASE_SCORES["unknown"])
    freshness_penalty = _freshness_penalty(freshness_seconds)
    fallback_penalty = 0.12 if is_fallback else 0.0
    synthetic_penalty = 0.2 if is_synthetic else 0.0
    verification_boost = 0.08 if is_verified and source_type not in {"manual_entry", "fixture"} else 0.0

    confidence = base_score - freshness_penalty - fallback_penalty - synthetic_penalty + verification_boost

    # Manual/fixture data should never appear production grade.
    if source_type in {"manual_entry", "fixture"}:
        confidence = min(confidence, 0.59)

    confidence = min(1.0, max(0.0, round(confidence, 4)))
    return SourceQualityResult(
        confidence=confidence,
        base_score=base_score,
        freshness_penalty=freshness_penalty,
        fallback_penalty=fallback_penalty,
        synthetic_penalty=synthetic_penalty,
        verification_boost=verification_boost,
    )


def _freshness_penalty(freshness_seconds: int | None) -> float:
    if freshness_seconds is None:
        return 0.08
    if freshness_seconds <= 3600:
        return 0.0
    if freshness_seconds <= 6 * 3600:
        return 0.03
    if freshness_seconds <= 24 * 3600:
        return 0.07
    if freshness_seconds <= 3 * 24 * 3600:
        return 0.12
    return 0.2
