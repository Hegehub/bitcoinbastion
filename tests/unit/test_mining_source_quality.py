from app.services.mining.source_quality import calculate_source_quality_confidence


def test_source_quality_official_verified_is_high() -> None:
    result = calculate_source_quality_confidence(
        source_type="official_pool_docs",
        freshness_seconds=600,
        is_verified=True,
    )
    assert 0.85 <= result.confidence <= 1.0
    assert result.verification_boost > 0


def test_source_quality_fixture_is_not_production_grade() -> None:
    result = calculate_source_quality_confidence(
        source_type="fixture",
        freshness_seconds=60,
        is_verified=True,
    )
    assert result.confidence < 0.6


def test_source_quality_unknown_with_penalties_drops_confidence() -> None:
    result = calculate_source_quality_confidence(
        source_type="unknown",
        freshness_seconds=None,
        is_fallback=True,
        is_synthetic=True,
    )
    assert 0.0 <= result.confidence <= 1.0
    assert result.fallback_penalty > 0
    assert result.synthetic_penalty > 0
    assert result.confidence < 0.2
