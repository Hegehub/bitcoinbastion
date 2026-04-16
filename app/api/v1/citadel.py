from fastapi import APIRouter

from app.schemas.base import ResponseEnvelope
from app.schemas.citadel import (
    CitadelAssessmentOut,
    CitadelAssessmentRecalculateIn,
    CitadelDependencyGraphOut,
    CitadelOverviewOut,
    CitadelPolicyChecksOut,
    CitadelRepairPlanOut,
    CitadelSimulationIn,
    CitadelSimulationOut,
    RecoveryReadinessOut,
)
from app.services.citadel import (
    CitadelAssessmentService,
    CitadelPolicyService,
    DisasterSimulationService,
    RepairPlanService,
    SovereigntyGraphService,
)

router = APIRouter(prefix="/citadel", tags=["citadel"])


@router.get("/overview", response_model=ResponseEnvelope[CitadelOverviewOut])
def citadel_overview(owner_type: str = "user", owner_id: int = 1) -> ResponseEnvelope[CitadelOverviewOut]:
    assessment = CitadelAssessmentService().build_assessment(owner_type=owner_type, owner_id=owner_id)
    recovery = CitadelAssessmentService().recovery_report(owner_id=owner_id)
    out = CitadelOverviewOut(
        owner_type=owner_type,
        owner_id=owner_id,
        overall_score=assessment.overall_score,
        recovery_readiness_score=recovery.recovery_readiness_score,
        top_findings=[f.title for f in assessment.critical_findings][:3],
        freshness={"assessment_generated_at": assessment.generated_at.isoformat()},
    )
    return ResponseEnvelope(data=out)


@router.get("/assessment", response_model=ResponseEnvelope[CitadelAssessmentOut])
def citadel_assessment(owner_type: str = "user", owner_id: int = 1) -> ResponseEnvelope[CitadelAssessmentOut]:
    data = CitadelAssessmentService().build_assessment(owner_type=owner_type, owner_id=owner_id)
    return ResponseEnvelope(data=data)


@router.post("/recalculate", response_model=ResponseEnvelope[CitadelAssessmentOut])
def recalculate_citadel(payload: CitadelAssessmentRecalculateIn) -> ResponseEnvelope[CitadelAssessmentOut]:
    data = CitadelAssessmentService().build_assessment(owner_type=payload.owner_type, owner_id=payload.owner_id)
    return ResponseEnvelope(data=data)


@router.get("/dependencies", response_model=ResponseEnvelope[CitadelDependencyGraphOut])
def citadel_dependencies(owner_id: int = 1) -> ResponseEnvelope[CitadelDependencyGraphOut]:
    data = CitadelDependencyGraphOut.model_validate(SovereigntyGraphService().build(owner_id=owner_id))
    return ResponseEnvelope(data=data)


@router.get("/recovery", response_model=ResponseEnvelope[RecoveryReadinessOut])
def citadel_recovery(owner_id: int = 1) -> ResponseEnvelope[RecoveryReadinessOut]:
    data = CitadelAssessmentService().recovery_report(owner_id=owner_id)
    return ResponseEnvelope(data=data)


@router.post("/simulations", response_model=ResponseEnvelope[CitadelSimulationOut])
def create_simulation(payload: CitadelSimulationIn) -> ResponseEnvelope[CitadelSimulationOut]:
    data = CitadelSimulationOut.model_validate(
        DisasterSimulationService().simulate(owner_id=payload.owner_id, scenario_code=payload.scenario_code)
    )
    return ResponseEnvelope(data=data)


@router.get("/simulations", response_model=ResponseEnvelope[list[CitadelSimulationOut]])
def list_simulations(owner_id: int = 1) -> ResponseEnvelope[list[CitadelSimulationOut]]:
    data = [
        CitadelSimulationOut.model_validate(
            DisasterSimulationService().simulate(owner_id=owner_id, scenario_code="loss_signer")
        )
    ]
    return ResponseEnvelope(data=data)


@router.get("/repair-plan", response_model=ResponseEnvelope[CitadelRepairPlanOut])
def citadel_repair_plan(owner_id: int = 1) -> ResponseEnvelope[CitadelRepairPlanOut]:
    data = CitadelRepairPlanOut.model_validate(RepairPlanService().build(owner_id=owner_id))
    return ResponseEnvelope(data=data)


@router.get("/policy-checks", response_model=ResponseEnvelope[CitadelPolicyChecksOut])
def citadel_policy_checks(owner_id: int = 1) -> ResponseEnvelope[CitadelPolicyChecksOut]:
    data = CitadelPolicyChecksOut.model_validate(CitadelPolicyService().evaluate(owner_id=owner_id))
    return ResponseEnvelope(data=data)
