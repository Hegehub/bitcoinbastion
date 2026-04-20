from app.db.models.explainability import EvidenceEdge, EvidenceNode
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
    assert result.recommendations[0].action_confidence > 0.8


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
    assert 0 <= result.recommendations[0].action_confidence <= 1


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

    edges = [
        EvidenceEdge(signal_id=3, from_node_key="n:high", to_node_key="n:mid", relation="supports", weight=0.8),
        EvidenceEdge(signal_id=3, from_node_key="n:mid", to_node_key="n:low", relation="correlates", weight=0.4),
    ]

    result = SignalRecommendationService().build(signal=signal, evidence_nodes=nodes, evidence_edges=edges)

    assert result.recommendations[0].evidence_refs == ["n:high", "n:mid", "n:low"]
    assert result.recommendations[0].evidence_paths == [
        "n:high --supports--> n:mid",
        "n:mid --correlates--> n:low",
    ]
    assert result.recommendations[0].action_confidence >= 0.8


def test_signal_recommendation_service_handles_malformed_horizons() -> None:
    signal = Signal(
        id=4,
        signal_type="news",
        severity="medium",
        score=0.6,
        confidence=0.2,
        title="Malformed horizons",
        summary="summary",
        explainability_json='{"horizons": {"short": "bad", "long": true, "dominant": "invalid"}}',
    )

    result = SignalRecommendationService().build(signal=signal)

    assert len(result.recommendations) == 1
    assert result.recommendations[0].horizon == "short"
    assert result.recommendations[0].priority == "low"


def test_signal_recommendation_service_deduplicates_evidence_and_policy_refs() -> None:
    signal = Signal(
        id=5,
        signal_type="news",
        severity="high",
        score=0.7,
        confidence=0.8,
        title="Dedup",
        summary="summary",
        source_refs_json='["n:1", "n:1", "n:2"]',
        details_json='{"policy_name": "default", "applied_policy_rules": ["default", "rule:x"]}',
        explainability_json='{"horizons": {"short": 0.9, "dominant": "short"}}',
    )

    result = SignalRecommendationService().build(signal=signal)

    assert result.recommendations[0].evidence_refs == ["n:1", "n:2"]
    assert result.recommendations[0].policy_refs == ["default", "rule:x"]


def test_signal_recommendation_service_normalizes_override_policy_refs() -> None:
    signal = Signal(
        id=6,
        signal_type="news",
        severity="high",
        score=0.7,
        confidence=0.8,
        title="Override policy refs",
        summary="summary",
        explainability_json='{"horizons": {"short": 0.9, "dominant": "short"}}',
    )

    result = SignalRecommendationService().build(
        signal=signal,
        policy_refs=[" rule:a ", "", "rule:a", "rule:b"],
    )

    assert result.recommendations[0].policy_refs == ["rule:a", "rule:b"]


def test_signal_recommendation_service_ignores_incomplete_evidence_edges() -> None:
    signal = Signal(
        id=7,
        signal_type="news",
        severity="medium",
        score=0.7,
        confidence=0.8,
        title="Edges",
        summary="summary",
        explainability_json='{"horizons": {"short": 0.9, "dominant": "short"}}',
    )
    nodes = [EvidenceNode(signal_id=7, node_key="n:1", weight=1.0)]
    edges = [
        EvidenceEdge(signal_id=7, from_node_key="n:1", to_node_key="n:2", relation="", weight=1.0),
        EvidenceEdge(signal_id=7, from_node_key="n:1", to_node_key="n:2", relation="supports", weight=1.0),
    ]

    result = SignalRecommendationService().build(signal=signal, evidence_nodes=nodes, evidence_edges=edges)

    assert result.recommendations[0].evidence_paths == ["n:1 --supports--> n:2"]


def test_signal_recommendation_service_handles_invalid_confidence_type() -> None:
    signal = Signal(
        id=8,
        signal_type="news",
        severity="high",
        score=0.7,
        confidence=0.6,
        title="Confidence override",
        summary="summary",
        source_refs_json='["n:1", "n:2", "n:3"]',
        explainability_json='{"horizons": {"short": 0.9, "dominant": "short"}}',
    )
    signal.confidence = "oops"  # type: ignore[assignment]

    result = SignalRecommendationService().build(signal=signal)

    assert result.recommendations[0].action_confidence == 0.15


def test_signal_recommendation_service_policy_refs_cap_after_dedup() -> None:
    signal = Signal(
        id=9,
        signal_type="news",
        severity="high",
        score=0.8,
        confidence=0.7,
        title="Policy dedupe cap",
        summary="summary",
        details_json='{"policy_name":"p1","applied_policy_rules":["p1","p2","p2","p3","p4"]}',
        explainability_json='{"horizons":{"short":0.9,"dominant":"short"}}',
    )

    result = SignalRecommendationService().build(signal=signal)

    assert result.recommendations[0].policy_refs == ["p1", "p2", "p3"]


def test_signal_recommendation_service_collects_unique_paths_up_to_cap() -> None:
    signal = Signal(
        id=10,
        signal_type="news",
        severity="medium",
        score=0.5,
        confidence=0.6,
        title="Path cap",
        summary="summary",
        explainability_json='{"horizons":{"short":0.9,"dominant":"short"}}',
    )
    nodes = [
        EvidenceNode(signal_id=10, node_key="n:1", weight=1.0),
        EvidenceNode(signal_id=10, node_key="n:2", weight=0.9),
    ]
    edges = [
        EvidenceEdge(signal_id=10, from_node_key="n:1", to_node_key="n:2", relation="supports", weight=1.0),
        EvidenceEdge(signal_id=10, from_node_key="n:1", to_node_key="n:2", relation="supports", weight=0.8),
        EvidenceEdge(signal_id=10, from_node_key="n:2", to_node_key="n:3", relation="correlates", weight=0.7),
        EvidenceEdge(signal_id=10, from_node_key="n:1", to_node_key="n:4", relation="explains", weight=0.6),
    ]

    result = SignalRecommendationService().build(signal=signal, evidence_nodes=nodes, evidence_edges=edges)

    assert result.recommendations[0].evidence_paths == [
        "n:1 --supports--> n:2",
        "n:2 --correlates--> n:3",
        "n:1 --explains--> n:4",
    ]


def test_signal_recommendation_service_respects_empty_policy_override() -> None:
    signal = Signal(
        id=11,
        signal_type="news",
        severity="high",
        score=0.9,
        confidence=0.9,
        title="Empty override",
        summary="summary",
        details_json='{"policy_name":"default","applied_policy_rules":["rule:1"]}',
        explainability_json='{"horizons":{"short":0.9,"dominant":"short"}}',
    )

    result = SignalRecommendationService().build(signal=signal, policy_refs=[])

    assert result.recommendations[0].policy_refs == []
