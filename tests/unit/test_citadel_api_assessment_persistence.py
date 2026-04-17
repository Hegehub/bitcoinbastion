from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.citadel import CitadelAssessmentOut


def _sample_assessment(owner_id: int) -> CitadelAssessmentOut:
    now = datetime.now(UTC)
    return CitadelAssessmentOut(
        id=10,
        owner_type="user",
        owner_id=owner_id,
        overall_score=88.0,
        custody_resilience_score=87.0,
        recovery_readiness_score=76.0,
        privacy_resilience_score=70.0,
        treasury_resilience_score=80.0,
        vendor_independence_score=68.0,
        inheritance_readiness_score=82.0,
        fee_survivability_score=74.0,
        policy_maturity_score=83.0,
        operational_hygiene_score=90.0,
        critical_findings=[],
        warnings=[],
        recommendations=[],
        explainability={},
        freshness={},
        generated_at=now,
        created_at=now,
        updated_at=now,
    )


def test_citadel_assessment_prefers_cached_snapshot(monkeypatch) -> None:
    cached_schema = _sample_assessment(owner_id=42)
    fresh_row = type("Row", (), {"generated_at": datetime.now(UTC)})()

    monkeypatch.setattr(
        "app.api.v1.citadel.CitadelAssessmentRepository.latest",
        lambda self, owner_type, owner_id: fresh_row,
    )
    monkeypatch.setattr(
        "app.api.v1.citadel.CitadelAssessmentRepository.to_schema",
        lambda self, row: cached_schema,
    )
    monkeypatch.setattr(
        "app.api.v1.citadel.CitadelAssessmentService.build_assessment",
        lambda self, owner_type, owner_id: (_ for _ in ()).throw(AssertionError("unexpected recalculation")),
    )

    client = TestClient(app)
    response = client.get("/api/v1/citadel/assessment", params={"owner_type": "user", "owner_id": 42})

    assert response.status_code == 200
    assert response.json()["data"]["id"] == 10
    assert response.json()["data"]["owner_id"] == 42
    assert response.json()["data"]["freshness"]["cache_source"] == "cache"
    assert response.json()["data"]["freshness"]["cache_age_seconds"] >= 0


def test_citadel_assessment_recalculates_when_snapshot_stale(monkeypatch) -> None:
    stale_row = type("Row", (), {"generated_at": datetime.now(UTC) - timedelta(hours=72)})()
    generated = _sample_assessment(owner_id=55)
    saved: dict[str, int] = {"count": 0}

    monkeypatch.setattr(
        "app.api.v1.citadel.CitadelAssessmentRepository.latest",
        lambda self, owner_type, owner_id: stale_row,
    )
    monkeypatch.setattr(
        "app.api.v1.citadel.CitadelAssessmentService.build_assessment",
        lambda self, owner_type, owner_id: generated,
    )
    monkeypatch.setattr(
        "app.api.v1.citadel.CitadelAssessmentRepository.save",
        lambda self, assessment: saved.__setitem__("count", saved["count"] + 1),
    )

    client = TestClient(app)
    response = client.get("/api/v1/citadel/assessment", params={"owner_type": "user", "owner_id": 55})

    assert response.status_code == 200
    assert response.json()["data"]["owner_id"] == 55
    assert response.json()["data"]["freshness"]["cache_source"] == "recomputed"
    assert response.json()["data"]["freshness"]["recompute_reason"] == "stale_or_miss"
    assert saved["count"] == 1


def test_citadel_assessment_force_refresh_ignores_fresh_cache(monkeypatch) -> None:
    fresh_row = type("Row", (), {"generated_at": datetime.now(UTC)})()
    generated = _sample_assessment(owner_id=56)

    monkeypatch.setattr(
        "app.api.v1.citadel.CitadelAssessmentRepository.latest",
        lambda self, owner_type, owner_id: fresh_row,
    )
    monkeypatch.setattr(
        "app.api.v1.citadel.CitadelAssessmentService.build_assessment",
        lambda self, owner_type, owner_id: generated,
    )

    client = TestClient(app)
    response = client.get(
        "/api/v1/citadel/assessment",
        params={"owner_type": "user", "owner_id": 56, "force_refresh": True},
    )

    assert response.status_code == 200
    assert response.json()["data"]["owner_id"] == 56
    assert response.json()["data"]["freshness"]["cache_source"] == "recomputed"
    assert response.json()["data"]["freshness"]["recompute_reason"] == "forced"


def test_citadel_recalculate_persists_snapshot(monkeypatch) -> None:
    generated = _sample_assessment(owner_id=99)
    saved: dict[str, int] = {"count": 0}

    monkeypatch.setattr(
        "app.api.v1.citadel.CitadelAssessmentService.build_assessment",
        lambda self, owner_type, owner_id: generated,
    )
    monkeypatch.setattr(
        "app.api.v1.citadel.CitadelAssessmentRepository.save",
        lambda self, assessment: saved.__setitem__("count", saved["count"] + 1),
    )

    client = TestClient(app)
    response = client.post("/api/v1/citadel/recalculate", json={"owner_type": "user", "owner_id": 99})

    assert response.status_code == 200
    assert response.json()["data"]["owner_id"] == 99
    assert saved["count"] == 1
