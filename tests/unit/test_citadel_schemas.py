from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.models.citadel_assessment import CitadelAssessment
from app.schemas.citadel import CitadelAssessmentOut, CitadelAssessmentRecalculateIn


def test_citadel_assessment_model_persists_defaults() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)

    with Session(engine) as db:
        row = CitadelAssessment(owner_type="user", owner_id=7, overall_score=72.5)
        db.add(row)
        db.commit()
        db.refresh(row)

        assert row.id > 0
        assert row.critical_findings_json == "[]"
        assert row.explainability_json == "{}"


def test_citadel_assessment_schema_validates_and_serializes() -> None:
    payload = CitadelAssessmentOut(
        id=1,
        owner_type="user",
        owner_id=1,
        overall_score=80,
        custody_resilience_score=82,
        recovery_readiness_score=79,
        privacy_resilience_score=76,
        treasury_resilience_score=84,
        vendor_independence_score=88,
        inheritance_readiness_score=70,
        fee_survivability_score=75,
        policy_maturity_score=83,
        operational_hygiene_score=81,
        critical_findings=[],
        warnings=[],
        recommendations=["Rotate signer backup drills quarterly"],
        explainability={"drivers": ["recovery_artifacts", "signer_diversity"]},
        freshness={"wallet_health_hours": 4},
        generated_at=datetime.utcnow(),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    dumped = payload.model_dump()
    assert dumped["overall_score"] == 80
    assert dumped["recommendations"]


def test_citadel_recalculate_input_enforces_owner_id() -> None:
    valid = CitadelAssessmentRecalculateIn(owner_type="user", owner_id=3)
    assert valid.owner_id == 3
