from app.services.intelligence.confidence.impact_confidence_engine import ImpactConfidenceEngine


def test_high_confidence_band() -> None:
    r = ImpactConfidenceEngine().calculate_impact_confidence(
        btc_relevance_score=0.95,
        source_credibility_score=0.9,
        provider_confidence=0.9,
        price_move_strength=0.9,
        sentiment_direction_match=1.0,
        minutes_to_reaction=5,
        volatility_context_weight=1.0,
        event_confirmation_weight=0.9,
        provider_count=3,
        stale=False,
        simultaneous_events=1,
    )
    assert r["confidence_band"] in {"high", "very_high"}


def test_false_signal_detected() -> None:
    r = ImpactConfidenceEngine().calculate_impact_confidence(
        btc_relevance_score=0.9,
        source_credibility_score=0.8,
        provider_confidence=0.4,
        price_move_strength=0.1,
        sentiment_direction_match=0.5,
        minutes_to_reaction=60,
        volatility_context_weight=0.8,
        event_confirmation_weight=0.2,
        provider_count=1,
        stale=True,
        simultaneous_events=2,
    )
    assert isinstance(r["false_signal_detected"], bool)
    assert "limitation" in r
