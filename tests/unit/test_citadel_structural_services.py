from app.services.citadel.disaster_simulation_service import DisasterSimulationService
from app.services.citadel.policy_maturity_service import CitadelPolicyService
from app.services.citadel.repair_plan_service import RepairPlanService
from app.services.citadel.sovereignty_graph_service import SovereigntyGraphService


def test_sovereignty_graph_service_flags_spof() -> None:
    out = SovereigntyGraphService().build(owner_id=5)
    assert out["nodes"]
    assert out["single_points_of_failure"]
    assert any(node["node_type"] == "policy" for node in out["nodes"])
    assert any(node["node_type"] == "coordinator" for node in out["nodes"])


def test_sovereignty_graph_service_multisig_reduces_signer_spof() -> None:
    out = SovereigntyGraphService().build(
        owner_id=7,
        wallet_type="multisig-2of3",
        has_descriptor=True,
        has_recent_health_report=True,
    )
    signing_spofs = [
        edge for edge in out["single_points_of_failure"] if edge["dependency_type"] == "signing"
    ]
    assert not signing_spofs
    assert out["confidence"] >= 0.8


def test_disaster_simulation_service_loss_signer_degrades_survivability() -> None:
    out = DisasterSimulationService().simulate(owner_id=5, scenario_code="loss_signer")
    assert out["survivability_score"] < 0.5
    assert out["blocked_paths"]
    assert out["explainability"]["rule_set"] == "citadel_disaster_v3"


def test_disaster_simulation_service_is_deterministic_for_same_input() -> None:
    first = DisasterSimulationService().simulate(owner_id=9, scenario_code="backup_loss")
    second = DisasterSimulationService().simulate(owner_id=9, scenario_code="backup_loss")
    assert first["survivability_score"] == second["survivability_score"]
    assert first["blocked_paths"] == second["blocked_paths"]
    assert first["critical_failure_points"] == second["critical_failure_points"]


def test_disaster_simulation_service_supports_extended_scenarios() -> None:
    scenarios = [
        "descriptor_corruption",
        "inheritance_trigger",
        "high_fee_emergency_spend",
        "provider_outage",
        "recovery_instruction_loss",
        "weak_finality_stress",
    ]
    for scenario in scenarios:
        out = DisasterSimulationService().simulate(owner_id=11, scenario_code=scenario)
        assert out["scenario_code"] == scenario
        assert out["blocked_paths"]
        assert out["recommended_remediations"]
        assert out["confidence"] >= 0.52
        assert out["explainability"]["affected_dependency_types"]


def test_disaster_descriptor_corruption_reflects_descriptor_penalty() -> None:
    out = DisasterSimulationService().simulate(owner_id=12, scenario_code="descriptor_corruption")
    assert out["explainability"]["descriptor_penalty"] >= 0
    assert out["explainability"]["descriptor_completeness_score"] <= 1.0
    assert out["blocked_paths"]


def test_repair_plan_service_returns_prioritized_items() -> None:
    out = RepairPlanService().build(owner_id=5)
    assert out["items"]
    assert out["items"][0]["priority_score"] >= out["items"][1]["priority_score"]
    assert "dependency_area" in out["items"][0]
    assert "expected_resilience_improvement" in out["items"][0]
    assert "effort_estimate" in out["items"][0]
    assert out["items"][0]["evidence_refs"]


def test_repair_plan_service_maps_items_to_recovery_and_inheritance_evidence() -> None:
    out = RepairPlanService().build(owner_id=21)
    areas = {item["dependency_area"] for item in out["items"]}
    assert "recovery_artifacts" in areas or "verification_freshness" in areas
    assert "inheritance" in areas or "operations" in areas or "descriptor" in areas


def test_policy_service_returns_maturity_payload() -> None:
    out = CitadelPolicyService().evaluate(owner_id=5)
    assert out["maturity"] in {"moderate", "weak"}
    assert out["gaps"]


def test_disaster_weak_finality_scenario_surfaces_chain_penalty() -> None:
    out = DisasterSimulationService().simulate(owner_id=15, scenario_code="weak_finality_stress")
    assert out["scenario_code"] == "weak_finality_stress"
    assert out["explainability"]["chain_state_penalty"] > 0
    assert out["explainability"]["chain_state_finality_band"] in {"weak", "moderate", "strong"}
