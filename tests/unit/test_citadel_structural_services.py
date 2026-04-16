from app.services.citadel.disaster_simulation_service import DisasterSimulationService
from app.services.citadel.policy_maturity_service import CitadelPolicyService
from app.services.citadel.repair_plan_service import RepairPlanService
from app.services.citadel.sovereignty_graph_service import SovereigntyGraphService


def test_sovereignty_graph_service_flags_spof() -> None:
    out = SovereigntyGraphService().build(owner_id=5)
    assert out["nodes"]
    assert out["single_points_of_failure"]


def test_disaster_simulation_service_loss_signer_degrades_survivability() -> None:
    out = DisasterSimulationService().simulate(owner_id=5, scenario_code="loss_signer")
    assert out["survivability_score"] < 0.5
    assert out["blocked_paths"]


def test_repair_plan_service_returns_prioritized_items() -> None:
    out = RepairPlanService().build(owner_id=5)
    assert out["items"]
    assert out["items"][0]["priority_score"] >= out["items"][1]["priority_score"]


def test_policy_service_returns_maturity_payload() -> None:
    out = CitadelPolicyService().evaluate(owner_id=5)
    assert out["maturity"] in {"moderate", "weak"}
    assert out["gaps"]
