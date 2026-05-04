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
    signing_spofs = [edge for edge in out["single_points_of_failure"] if edge["dependency_type"] == "signing"]
    assert not signing_spofs
    assert out["confidence"] >= 0.8


def test_disaster_simulation_service_loss_signer_degrades_survivability() -> None:
    out = DisasterSimulationService().simulate(owner_id=5, scenario_code="loss_signer")
    assert out["survivability_score"] < 0.5
    assert out["blocked_paths"]
    assert out["explainability"]["rule_set"] == "citadel_disaster_v2"


def test_disaster_simulation_service_is_deterministic_for_same_input() -> None:
    first = DisasterSimulationService().simulate(owner_id=9, scenario_code="backup_loss")
    second = DisasterSimulationService().simulate(owner_id=9, scenario_code="backup_loss")
    assert first["survivability_score"] == second["survivability_score"]
    assert first["blocked_paths"] == second["blocked_paths"]
    assert first["critical_failure_points"] == second["critical_failure_points"]


def test_repair_plan_service_returns_prioritized_items() -> None:
    out = RepairPlanService().build(owner_id=5)
    assert out["items"]
    assert out["items"][0]["priority_score"] >= out["items"][1]["priority_score"]


def test_policy_service_returns_maturity_payload() -> None:
    out = CitadelPolicyService().evaluate(owner_id=5)
    assert out["maturity"] in {"moderate", "weak"}
    assert out["gaps"]
