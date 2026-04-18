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


def test_chain_state_service_marks_weak_finality_for_unconfirmed_tip() -> None:
    out = ChainStateService().evaluate(
        tip_height=900_000,
        observed_block_height=900_000,
        headers_height=900_004,
    )

    assert out.confirmation_depth == 1
    assert out.reorg_risk_score >= 0.7
    assert out.finality_band == "weak"
