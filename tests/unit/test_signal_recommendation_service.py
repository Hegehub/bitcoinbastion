from app.db.models.explainability import EvidenceNode
from app.db.models.signal import Signal
from app.services.agentic.recommendation_service import SignalRecommendationService


def test_signal_recommendation_service_returns_high_priority_for_high_severity() -> None:
    signal = Signal(
        id=1,
        signal_type="onchain",
        severity="high",
        score=0.9,
        confidence=0.8,
        title="High impact",
        summary="summary",
        source_refs_json='["news:1", "onchain:2"]',
        details_json='{"policy_name": "default", "applied_policy_rules": ["min_wallet_health_score"]}',
        explainability_json='{"horizons": {"short": 0.8, "medium": 0.7, "long": 0.4, "dominant": "short"}}',
    )

    result = SignalRecommendationService().build(signal)

    assert result.signal_id == 1
    assert result.generated_by == "signal_recommendation_v2"
    assert result.recommendations
    assert result.recommendations[0].priority == "high"
    assert result.recommendations[0].evidence_refs == ["news:1", "onchain:2"]
    assert result.recommendations[0].policy_refs == ["default", "min_wallet_health_score"]


def test_signal_recommendation_service_returns_monitoring_for_low_impact() -> None:
    signal = Signal(
        id=2,
        signal_type="news",
        severity="low",
        score=0.2,
        confidence=0.3,
        title="Low impact",
        summary="summary",
        explainability_json='{"horizons": {"short": 0.2, "medium": 0.2, "long": 0.1, "dominant": "short"}}',
    )

    result = SignalRecommendationService().build(signal)

    assert len(result.recommendations) == 1
    assert "Monitor" in result.recommendations[0].action


def test_signal_recommendation_service_prefers_weighted_evidence_nodes() -> None:
    signal = Signal(
        id=3,
        signal_type="news",
        severity="medium",
        score=0.6,
        confidence=0.7,
        title="Evidence rich",
        summary="summary",
        source_refs_json='["fallback:source"]',
        explainability_json='{"horizons": {"short": 0.7, "medium": 0.6, "long": 0.2, "dominant": "short"}}',
    )
    nodes = [
        EvidenceNode(signal_id=3, node_key="n:low", weight=0.1),
        EvidenceNode(signal_id=3, node_key="n:high", weight=0.9),
        EvidenceNode(signal_id=3, node_key="n:mid", weight=0.5),
    ]

    result = SignalRecommendationService().build(signal=signal, evidence_nodes=nodes)

    assert result.recommendations[0].evidence_refs == ["n:high", "n:mid", "n:low"]
