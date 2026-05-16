from datetime import UTC, datetime
import json

from app.db.models.news import NewsArticle
from app.db.models.onchain import OnchainEvent
from app.services.alerts.signal_engine import SignalEngine


def test_signal_engine_records_news_latency(monkeypatch) -> None:
    observed: list[dict[str, object]] = []
    monkeypatch.setattr(
        "app.services.alerts.signal_engine.observe_signal_latency",
        lambda **kwargs: observed.append(kwargs),
    )

    article = NewsArticle(
        source_id=1,
        title="BTC test",
        url="https://example.com/news",
        content_hash="h1",
        published_at=datetime.now(UTC),
        content_clean="content",
        summary="summary",
        btc_relevance_score=0.8,
        urgency_score=0.5,
        impact_score=0.7,
        confidence_score=0.9,
    )

    signal = SignalEngine().from_news(article, explainability={"reason": "unit-test"})

    assert signal.signal_type == "news"
    assert observed
    assert observed[0]["source"] == "news"
    assert float(observed[0]["duration_seconds"]) >= 0.0


def test_signal_engine_records_onchain_latency(monkeypatch) -> None:
    observed: list[dict[str, object]] = []
    monkeypatch.setattr(
        "app.services.alerts.signal_engine.observe_signal_latency",
        lambda **kwargs: observed.append(kwargs),
    )

    event = OnchainEvent(
        event_type="large_transfer",
        txid="tx1",
        address="bc1qabc",
        value_sats=100_000,
        significance_score=0.65,
        confidence_score=0.8,
        tags_json='["whale"]',
    )

    signal = SignalEngine().from_onchain_event(event)

    assert signal.signal_type == "onchain"

    payload = signal.explainability_json
    assert "onchain_scoring_pipeline" in payload
    assert "source_type" in payload
    assert observed
    assert observed[0]["source"] == "onchain"
    assert float(observed[0]["duration_seconds"]) >= 0.0


def test_signal_engine_onchain_weak_finality_reduces_publishability_and_confidence() -> None:
    event = OnchainEvent(
        event_type="large_transfer",
        txid="tx-weak",
        address="bc1qweak",
        value_sats=2_000_000_000,
        significance_score=0.9,
        confidence_score=0.72,
        block_height=500_000,
        raw_payload_json=json.dumps(
            {
                "tip_height": 500_000,
                "headers_height": 500_003,
                "chain_state_source": "repository_fallback",
            }
        ),
    )

    signal = SignalEngine().from_onchain_event(event)
    explainability = json.loads(signal.explainability_json)

    assert signal.confidence < 0.72
    assert signal.is_published is False
    assert explainability["chain_state"]["finality_band"] == "weak"
    assert explainability["recommendations"]


def test_signal_engine_onchain_strong_finality_preserves_publishability() -> None:
    event = OnchainEvent(
        event_type="large_transfer",
        txid="tx-strong",
        address="bc1qstrong",
        value_sats=2_000_000_000,
        significance_score=0.9,
        confidence_score=0.9,
        block_height=500_000,
        raw_payload_json=json.dumps(
            {
                "tip_height": 500_012,
                "headers_height": 500_012,
                "chain_state_source": "query",
            }
        ),
    )

    signal = SignalEngine().from_onchain_event(event)
    explainability = json.loads(signal.explainability_json)

    assert signal.is_published is True
    assert explainability["chain_state"]["finality_band"] == "strong"
    assert "risk_components" in explainability["chain_state"]
