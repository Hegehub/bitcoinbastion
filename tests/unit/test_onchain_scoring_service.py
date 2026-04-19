from datetime import UTC, datetime

from app.integrations.bitcoin.provider import ChainEvent
from app.services.scoring.onchain_scoring import OnchainScoringService


def test_onchain_scoring_boosts_dormant_and_watched_activity() -> None:
    event = ChainEvent(
        event_type="large_transfer",
        txid="abc123",
        address="bc1qwatch",
        value_sats=1_250_000_000,
        block_height=910000,
        observed_at=datetime.now(UTC),
        payload={"dormancy_days": 1800, "watched_entity": 1},
    )

    score = OnchainScoringService().score(event)

    assert score.significance > 0.7
    assert score.confidence > 0.8
    assert score.explainability["reason"] == "onchain_significance_baseline"
    assert "watched_entity" in score.tags
    assert "dormant_coins" in score.tags


def test_onchain_scoring_handles_minimal_payload() -> None:
    event = ChainEvent(
        event_type="transfer",
        txid="tx-min",
        address="bc1qmin",
        value_sats=20_000,
        block_height=910001,
        observed_at=datetime.now(UTC),
        payload={},
    )

    score = OnchainScoringService().score(event)

    assert 0.0 <= score.significance <= 1.0
    assert 0.0 <= score.confidence <= 1.0
    assert score.tags == ["transfer"]
