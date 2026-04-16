from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import db_session
from app.db.repositories.citadel_repository import CitadelAssessmentRepository
from app.schemas.base import ResponseEnvelope
from app.schemas.citadel import (
    CitadelAssessmentOut,
    CitadelAssessmentRecalculateIn,
    CitadelDependencyGraphOut,
    CitadelFreshnessOut,
    CitadelOverviewOut,
    CitadelInheritanceOut,
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
    InheritanceVerificationService,
)

router = APIRouter(prefix="/citadel", tags=["citadel"])


def _is_snapshot_fresh(*, generated_at: datetime, max_age_hours: int) -> bool:
    generated_utc = generated_at if generated_at.tzinfo is not None else generated_at.replace(tzinfo=UTC)
    return generated_utc >= (datetime.now(UTC) - timedelta(hours=max_age_hours))


def _cache_age_seconds(*, generated_at: datetime) -> int:
    generated_utc = generated_at if generated_at.tzinfo is not None else generated_at.replace(tzinfo=UTC)
    return max(0, int((datetime.now(UTC) - generated_utc).total_seconds()))


def _load_assessment(
    *,
    owner_type: str,
    owner_id: int,
    force_refresh: bool,
    max_age_hours: int,
    db: Session,
) -> CitadelAssessmentOut:
    repo = CitadelAssessmentRepository(db)
    cached = repo.latest(owner_type=owner_type, owner_id=owner_id)
    cached_is_fresh = cached is not None and _is_snapshot_fresh(generated_at=cached.generated_at, max_age_hours=max_age_hours)
    if cached is not None and cached_is_fresh and not force_refresh:
        cached_data = repo.to_schema(cached)
        cached_freshness = CitadelFreshnessOut.model_validate(cached_data.freshness)
        return cached_data.model_copy(
            update={
                "freshness": CitadelFreshnessOut(
                    **{
                        **cached_freshness.model_dump(exclude_none=True),
                        "cache_source": "cache",
                        "cache_age_seconds": _cache_age_seconds(generated_at=cached.generated_at),
                    }
                ),
            }
        )

    data = CitadelAssessmentService().build_assessment(owner_type=owner_type, owner_id=owner_id)
    repo.save(assessment=data)
    reason = "forced" if force_refresh else "stale_or_miss"
    freshness = CitadelFreshnessOut.model_validate(data.freshness)
    return data.model_copy(
        update={
            "freshness": CitadelFreshnessOut(
                **{
                    **freshness.model_dump(exclude_none=True),
                    "cache_source": "recomputed",
                    "recompute_reason": reason,
                }
            ),
        }
    )


@router.get("/overview", response_model=ResponseEnvelope[CitadelOverviewOut])
def citadel_overview(
    owner_type: str = "user",
    owner_id: int = 1,
    force_refresh: bool = False,
    max_age_hours: int = Query(default=24, ge=1, le=24 * 30),
    db: Session = Depends(db_session),
) -> ResponseEnvelope[CitadelOverviewOut]:
    assessment = _load_assessment(
        owner_type=owner_type,
        owner_id=owner_id,
        force_refresh=force_refresh,
        max_age_hours=max_age_hours,
        db=db,
    )
    freshness = CitadelFreshnessOut.model_validate(assessment.freshness)
    out = CitadelOverviewOut(
        owner_type=owner_type,
        owner_id=owner_id,
        overall_score=assessment.overall_score,
        recovery_readiness_score=round(assessment.recovery_readiness_score / 100, 3),
        top_findings=[f.title for f in [*assessment.critical_findings, *assessment.warnings]][:3],
        freshness=CitadelFreshnessOut(
            **{
                **freshness.model_dump(exclude_none=True),
                "assessment_generated_at": assessment.generated_at.isoformat(),
            }
        ),
    )
    return ResponseEnvelope(data=out)


@router.get("/assessment", response_model=ResponseEnvelope[CitadelAssessmentOut])
def citadel_assessment(
    owner_type: str = "user",
    owner_id: int = 1,
    force_refresh: bool = False,
    max_age_hours: int = Query(default=24, ge=1, le=24 * 30),
    db: Session = Depends(db_session),
) -> ResponseEnvelope[CitadelAssessmentOut]:
    return ResponseEnvelope(
        data=_load_assessment(
            owner_type=owner_type,
            owner_id=owner_id,
            force_refresh=force_refresh,
            max_age_hours=max_age_hours,
            db=db,
        )
    )


@router.post("/recalculate", response_model=ResponseEnvelope[CitadelAssessmentOut])
def recalculate_citadel(
    payload: CitadelAssessmentRecalculateIn,
    db: Session = Depends(db_session),
) -> ResponseEnvelope[CitadelAssessmentOut]:
    repo = CitadelAssessmentRepository(db)
    data = CitadelAssessmentService().build_assessment(owner_type=payload.owner_type, owner_id=payload.owner_id)
    repo.save(assessment=data)
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


@router.get("/inheritance", response_model=ResponseEnvelope[CitadelInheritanceOut])
def citadel_inheritance(owner_id: int = 1) -> ResponseEnvelope[CitadelInheritanceOut]:
    data = CitadelInheritanceOut.model_validate(InheritanceVerificationService().evaluate(owner_id=owner_id))
    return ResponseEnvelope(data=data)


@router.get("/repair-plan", response_model=ResponseEnvelope[CitadelRepairPlanOut])
def citadel_repair_plan(owner_id: int = 1) -> ResponseEnvelope[CitadelRepairPlanOut]:
    data = CitadelRepairPlanOut.model_validate(RepairPlanService().build(owner_id=owner_id))
    return ResponseEnvelope(data=data)


@router.get("/policy-checks", response_model=ResponseEnvelope[CitadelPolicyChecksOut])
def citadel_policy_checks(owner_id: int = 1) -> ResponseEnvelope[CitadelPolicyChecksOut]:
    data = CitadelPolicyChecksOut.model_validate(CitadelPolicyService().evaluate(owner_id=owner_id))
    return ResponseEnvelope(data=data)
