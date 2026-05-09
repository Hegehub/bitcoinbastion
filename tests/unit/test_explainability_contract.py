from app.services.blockchain.chain_state_service import ChainStateService
from app.services.citadel.citadel_assessment_service import CitadelAssessmentService
from app.services.explainability.contract import build_explainability_contract


def test_explainability_contract_builder_shape() -> None:
    out = build_explainability_contract(
        domain="protocol_layer",
        confidence=0.66,
        freshness={"freshness_band": "stale"},
        source_type="provider",
        provider_name="esplora",
        is_fallback=False,
        limitations=["advisory"],
        signals={"depth": 3},
    )
    assert out["version"] == "exp_v1"
    assert out["domain"] == "protocol_layer"
    assert out["confidence"] == 0.66
    assert out["freshness"]["freshness_band"] == "stale"


def test_chain_state_explainability_includes_contract() -> None:
    out = ChainStateService().evaluate(
        tip_height=100,
        observed_block_height=99,
        provider_tip_height=100,
        provider_confidence=0.8,
        provider_data_age_seconds=10,
        data_source="provider_probe",
    )
    contract = out.explainability["contract"]
    assert contract["domain"] == "protocol_layer"
    assert "limitations" in contract


def test_citadel_explainability_includes_contract() -> None:
    out = CitadelAssessmentService().build_assessment(owner_type="user", owner_id=91)
    contract = out.explainability.model_dump()["contract"]
    assert contract["domain"] == "citadel"
    assert "protocol_fallback_domains" in contract["signals"]
