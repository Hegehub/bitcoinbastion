from datetime import UTC, datetime

from app.integrations.bitcoin.provider import ChainEvent
from app.services.blockchain.chain_state_service import ChainStateService
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


def test_onchain_scoring_applies_chain_state_penalty_for_weak_finality() -> None:
    event = ChainEvent(
        event_type="large_transfer",
        txid="weak-finality",
        address="bc1qweak",
        value_sats=1_100_000_000,
        block_height=910010,
        observed_at=datetime.now(UTC),
        payload={},
    )
    weak_state = ChainStateService().evaluate(
        tip_height=910010,
        observed_block_height=910010,
        headers_height=910013,
        data_source="repository_fallback",
    )

    weak_score = OnchainScoringService().score(event, chain_state=weak_state)
    base_score = OnchainScoringService().score(event)

    assert weak_score.confidence < base_score.confidence
    assert weak_score.explainability["chain_state_penalty"] > 0
    assert "finality_weak" in weak_score.tags


def test_onchain_scoring_applies_chain_state_bonus_for_strong_finality() -> None:
    event = ChainEvent(
        event_type="large_transfer",
        txid="strong-finality",
        address="bc1qstrong",
        value_sats=1_100_000_000,
        block_height=910010,
        observed_at=datetime.now(UTC),
        payload={},
    )
    strong_state = ChainStateService().evaluate(
        tip_height=910022,
        observed_block_height=910010,
        headers_height=910022,
        data_source="query",
    )

    strong_score = OnchainScoringService().score(event, chain_state=strong_state)
    assert strong_score.explainability["chain_state_bonus"] >= 0
    assert "finality_strong" in strong_score.tags


def test_onchain_scoring_exposes_evidence_chain() -> None:
    from datetime import UTC, datetime
    from app.integrations.bitcoin.provider import ChainEvent

    event = ChainEvent(
        event_type="large_transfer",
        txid="ev1",
        address="bc1q1",
        value_sats=2_000_000,
        block_height=100,
        observed_at=datetime.now(UTC),
        payload={"source_type": "provider"},
    )
    state = ChainStateService().evaluate(tip_height=101, observed_block_height=100, data_source="provider_probe")
    out = OnchainScoringService().score(event, chain_state=state)
    chain = out.explainability["evidence_chain"]
    assert len(chain) >= 2
    assert chain[0]["domain"] == "protocol"
    assert chain[1]["domain"] == "scoring"


def test_onchain_scoring_degrades_with_fallback_stale_chain_state() -> None:
    from datetime import UTC, datetime
    from app.integrations.bitcoin.provider import ChainEvent

    event = ChainEvent(event_type="large_transfer", txid="ev2", address="bc1q2", value_sats=2_000_000_000, block_height=100, observed_at=datetime.now(UTC), payload={"source_type": "provider"})
    fresh = ChainStateService().evaluate(tip_height=101, observed_block_height=100, data_source="provider_probe", provider_data_age_seconds=10)
    stale_fallback = ChainStateService().evaluate(tip_height=101, observed_block_height=100, data_source="provider_fallback", provider_data_age_seconds=1200)
    fresh_score = OnchainScoringService().score(event, chain_state=fresh)
    stale_score = OnchainScoringService().score(event, chain_state=stale_fallback)
    assert stale_score.confidence < fresh_score.confidence
    assert stale_score.explainability["contract"]["is_fallback"] is True
    assert "audit_packet" in stale_score.explainability
    assert stale_score.explainability["audit_packet"]["packet_type"] == "high_risk_signal"
