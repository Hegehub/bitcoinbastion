from app.services.blockchain.chain_state_service import ChainStateService


def test_chain_state_service_marks_strong_finality_for_deep_confirmation() -> None:
    out = ChainStateService().evaluate(
        tip_height=900_000,
        observed_block_height=899_990,
        headers_height=900_000,
    )

    assert out.confirmation_depth >= 6
    assert out.reorg_risk_score <= 0.2
    assert out.finality_score >= 0.8
    assert out.finality_band == "strong"
    assert out.explainability["calibration_version"] == "chain_state_v2"


def test_chain_state_service_marks_weak_finality_for_unconfirmed_tip() -> None:
    out = ChainStateService().evaluate(
        tip_height=900_000,
        observed_block_height=900_000,
        headers_height=900_004,
    )

    assert out.confirmation_depth == 1
    assert out.reorg_risk_score >= 0.7
    assert out.finality_band == "weak"
    assert out.explainability["derived"]["header_tip_gap_blocks"] == 4


def test_chain_state_service_penalizes_header_lag_both_directions() -> None:
    ahead = ChainStateService().evaluate(
        tip_height=900_000,
        observed_block_height=899_999,
        headers_height=900_003,
    )
    behind = ChainStateService().evaluate(
        tip_height=900_000,
        observed_block_height=899_999,
        headers_height=899_997,
    )

    assert ahead.reorg_risk_score > 0.0
    assert behind.reorg_risk_score > 0.0
