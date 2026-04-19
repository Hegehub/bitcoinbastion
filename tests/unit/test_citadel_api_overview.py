from datetime import UTC, datetime

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.citadel import CitadelAssessmentOut, CitadelFindingOut


def test_citadel_overview_uses_assessment_payload_without_secondary_recovery_call(monkeypatch) -> None:
    fixed_time = datetime.now(UTC)
    assessment = CitadelAssessmentOut(
        id=1,
        owner_type="user",
        owner_id=77,
        overall_score=82.5,
        custody_resilience_score=80.0,
        recovery_readiness_score=65.0,
        privacy_resilience_score=70.0,
        treasury_resilience_score=75.0,
        vendor_independence_score=60.0,
        inheritance_readiness_score=68.0,
        fee_survivability_score=74.0,
        policy_maturity_score=66.0,
        operational_hygiene_score=84.0,
        critical_findings=[
            CitadelFindingOut(title="Critical one", severity="critical", domain="recovery", detail="x")
        ],
        warnings=[CitadelFindingOut(title="Warning one", severity="warning", domain="policy", detail="y")],
        recommendations=[],
        explainability={},
        freshness={},
        generated_at=fixed_time,
        created_at=fixed_time,
        updated_at=fixed_time,
    )

    monkeypatch.setattr(
        "app.api.v1.citadel.CitadelAssessmentService.build_assessment",
        lambda self, owner_type, owner_id: assessment,
    )
    monkeypatch.setattr(
        "app.api.v1.citadel.CitadelAssessmentRepository.latest",
        lambda self, owner_type, owner_id: None,
    )
    monkeypatch.setattr(
        "app.api.v1.citadel.CitadelAssessmentRepository.save",
        lambda self, assessment: None,
    )
    monkeypatch.setattr(
        "app.api.v1.citadel.CitadelAssessmentService.recovery_report",
        lambda self, owner_id: (_ for _ in ()).throw(AssertionError("unexpected recovery_report call")),
    )

    client = TestClient(app)
    response = client.get("/api/v1/citadel/overview", params={"owner_type": "user", "owner_id": 77})

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["recovery_readiness_score"] == 0.65
    assert payload["top_findings"] == ["Critical one", "Warning one"]
    assert payload["freshness"]["cache_source"] == "recomputed"


def test_citadel_overview_surfaces_cache_metadata(monkeypatch) -> None:
    fixed_time = datetime.now(UTC)
    cached_assessment = CitadelAssessmentOut(
        id=2,
        owner_type="user",
        owner_id=88,
        overall_score=81.0,
        custody_resilience_score=81.0,
        recovery_readiness_score=70.0,
        privacy_resilience_score=70.0,
        treasury_resilience_score=70.0,
        vendor_independence_score=70.0,
        inheritance_readiness_score=70.0,
        fee_survivability_score=70.0,
        policy_maturity_score=70.0,
        operational_hygiene_score=70.0,
        critical_findings=[],
        warnings=[],
        recommendations=[],
        explainability={},
        freshness={},
        generated_at=fixed_time,
        created_at=fixed_time,
        updated_at=fixed_time,
    )
    row = type("Row", (), {"generated_at": fixed_time})()

    monkeypatch.setattr(
        "app.api.v1.citadel.CitadelAssessmentRepository.latest",
        lambda self, owner_type, owner_id: row,
    )
    monkeypatch.setattr(
        "app.api.v1.citadel.CitadelAssessmentRepository.to_schema",
        lambda self, value: cached_assessment,
    )
    monkeypatch.setattr(
        "app.api.v1.citadel.CitadelAssessmentService.build_assessment",
        lambda self, owner_type, owner_id: (_ for _ in ()).throw(AssertionError("unexpected recalculation")),
    )

    client = TestClient(app)
    response = client.get("/api/v1/citadel/overview", params={"owner_type": "user", "owner_id": 88})

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["freshness"]["cache_source"] == "cache"
    assert payload["freshness"]["cache_age_seconds"] >= 0
