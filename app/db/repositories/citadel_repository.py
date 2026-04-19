import json

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.models.citadel_assessment import CitadelAssessment
from app.schemas.citadel import CitadelAssessmentOut, CitadelFindingOut, CitadelFreshnessOut


class CitadelAssessmentRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def latest(self, *, owner_type: str, owner_id: int) -> CitadelAssessment | None:
        stmt = (
            select(CitadelAssessment)
            .where(CitadelAssessment.owner_type == owner_type)
            .where(CitadelAssessment.owner_id == owner_id)
            .order_by(CitadelAssessment.generated_at.desc())
            .limit(1)
        )
        try:
            return self.db.execute(stmt).scalar_one_or_none()
        except SQLAlchemyError:
            return None

    def save(self, *, assessment: CitadelAssessmentOut) -> CitadelAssessment | None:
        row = CitadelAssessment(
            owner_type=assessment.owner_type,
            owner_id=assessment.owner_id,
            overall_score=assessment.overall_score,
            custody_resilience_score=assessment.custody_resilience_score,
            recovery_readiness_score=assessment.recovery_readiness_score,
            privacy_resilience_score=assessment.privacy_resilience_score,
            treasury_resilience_score=assessment.treasury_resilience_score,
            vendor_independence_score=assessment.vendor_independence_score,
            inheritance_readiness_score=assessment.inheritance_readiness_score,
            fee_survivability_score=assessment.fee_survivability_score,
            policy_maturity_score=assessment.policy_maturity_score,
            operational_hygiene_score=assessment.operational_hygiene_score,
            critical_findings_json=json.dumps([item.model_dump() for item in assessment.critical_findings]),
            warnings_json=json.dumps([item.model_dump() for item in assessment.warnings]),
            recommendations_json=json.dumps(assessment.recommendations),
            explainability_json=json.dumps(assessment.explainability.model_dump()),
            freshness_json=json.dumps(assessment.freshness.model_dump(exclude_none=True)),
            generated_at=assessment.generated_at,
            created_at=assessment.created_at,
            updated_at=assessment.updated_at,
        )
        try:
            self.db.add(row)
            self.db.commit()
            self.db.refresh(row)
            return row
        except SQLAlchemyError:
            self.db.rollback()
            return None

    @staticmethod
    def to_schema(row: CitadelAssessment) -> CitadelAssessmentOut:
        return CitadelAssessmentOut(
            id=row.id,
            owner_type=row.owner_type,
            owner_id=row.owner_id,
            overall_score=row.overall_score,
            custody_resilience_score=row.custody_resilience_score,
            recovery_readiness_score=row.recovery_readiness_score,
            privacy_resilience_score=row.privacy_resilience_score,
            treasury_resilience_score=row.treasury_resilience_score,
            vendor_independence_score=row.vendor_independence_score,
            inheritance_readiness_score=row.inheritance_readiness_score,
            fee_survivability_score=row.fee_survivability_score,
            policy_maturity_score=row.policy_maturity_score,
            operational_hygiene_score=row.operational_hygiene_score,
            critical_findings=[CitadelFindingOut.model_validate(item) for item in json.loads(row.critical_findings_json)],
            warnings=[CitadelFindingOut.model_validate(item) for item in json.loads(row.warnings_json)],
            recommendations=list(json.loads(row.recommendations_json)),
            explainability=dict(json.loads(row.explainability_json)),
            freshness=CitadelFreshnessOut.model_validate(json.loads(row.freshness_json)),
            generated_at=row.generated_at,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )
