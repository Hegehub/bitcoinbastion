from app.services.blockchain.chain_state_service import ChainStateService


def test_chain_state_service_confirmation_depth_bands_are_conservative() -> None:
    service = ChainStateService()

    out_0 = service.evaluate(tip_height=900_000, observed_block_height=900_001)
    out_1 = service.evaluate(tip_height=900_000, observed_block_height=900_000)
    out_3 = service.evaluate(tip_height=900_000, observed_block_height=899_998)
    out_6 = service.evaluate(tip_height=900_000, observed_block_height=899_995)
    out_12 = service.evaluate(tip_height=900_000, observed_block_height=899_989)

    assert out_0.confirmation_depth == 0
    assert out_0.finality_band == "weak"
    assert out_1.confirmation_depth == 1
    assert out_1.finality_band == "weak"
    assert out_3.confirmation_depth == 3
    assert out_3.finality_band in {"weak", "moderate"}
    assert out_6.confirmation_depth == 6
    assert out_6.finality_band in {"moderate", "strong"}
    assert out_12.confirmation_depth == 12
    assert out_12.finality_band == "strong"


def test_chain_state_service_penalizes_header_mismatch() -> None:
    baseline = ChainStateService().evaluate(
        tip_height=900_000,
        observed_block_height=899_995,
        headers_height=900_000,
    )
    mismatch = ChainStateService().evaluate(
        tip_height=900_000,
        observed_block_height=899_995,
        headers_height=900_004,
    )

    assert mismatch.reorg_risk_score > baseline.reorg_risk_score
    assert mismatch.confidence_score < baseline.confidence_score


def test_chain_state_service_penalizes_stale_provider_data() -> None:
    fresh = ChainStateService().evaluate(
        tip_height=900_000,
        observed_block_height=899_998,
        provider_tip_height=900_000,
        provider_confidence=0.82,
        provider_data_age_seconds=20,
        data_source="provider_probe",
    )
    stale = ChainStateService().evaluate(
        tip_height=900_000,
        observed_block_height=899_998,
        provider_tip_height=899_996,
        provider_confidence=0.82,
        provider_data_age_seconds=1_200,
        data_source="provider_probe",
    )

    assert stale.reorg_risk_score > fresh.reorg_risk_score
    assert stale.confidence_score < fresh.confidence_score
    assert stale.freshness["provider_freshness_band"] == "very_stale"


def test_chain_state_service_explainability_includes_risk_components() -> None:
    out = ChainStateService().evaluate(
        tip_height=900_000,
        observed_block_height=899_999,
        headers_height=900_002,
        provider_tip_height=899_997,
        provider_confidence=0.7,
        provider_data_age_seconds=300,
        data_source="provider_probe",
    )

    assert out.explainability["calibration_version"] == "chain_state_v4_conservative"
    assert "risk_components" in out.explainability
    assert "stale_provider_risk_component" in out.explainability["risk_components"]
    assert out.explainability["scoring"]["note"].startswith("Conservative risk model")
