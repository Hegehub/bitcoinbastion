from app.services.citadel.sovereignty_graph_service import SovereigntyGraphService
from app.services.citadel.disaster_simulation_service import DisasterSimulationService
from app.services.citadel.inheritance_verification_service import InheritanceVerificationService
from app.services.citadel.repair_plan_service import RepairPlanService
from app.services.citadel.recovery_readiness_engine import RecoveryReadinessEngine
from app.services.citadel.recovery_artifact_service import RecoveryArtifactRecord

REQUIRED = [
    "synthetic_component",
    "synthetic_reason",
    "production_replacement_path",
    "confidence_penalty",
    "operator_warning",
    "evidence_refs",
    "limitations",
    "source_quality",
]


def _assert_fields(payload: dict[str, object]) -> None:
    for f in REQUIRED:
        assert f in payload


def test_synthetic_labels_present_across_outputs() -> None:
    _assert_fields(SovereigntyGraphService().build(owner_id=1))
    _assert_fields(
        DisasterSimulationService().simulate(owner_id=1, scenario_code="provider_outage")
    )
    _assert_fields(InheritanceVerificationService().evaluate(owner_id=1))
    _assert_fields(RepairPlanService().build(owner_id=1))
    rec = RecoveryReadinessEngine().evaluate(
        artifacts=[
            RecoveryArtifactRecord(
                artifact_type="descriptor", label="x", is_verified=False, required_for_recovery=True
            )
        ],
        has_descriptor=False,
        has_instructions=False,
        human_dependency_score=0.9,
    )
    _assert_fields(rec)
