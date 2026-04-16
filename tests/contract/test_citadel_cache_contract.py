from fastapi.testclient import TestClient

from app.main import app


def test_citadel_assessment_freshness_contract() -> None:
    client = TestClient(app)
    response = client.get(
        "/api/v1/citadel/assessment",
        params={"owner_type": "user", "owner_id": 321, "force_refresh": True},
    )

    assert response.status_code == 200
    freshness = response.json()["data"]["freshness"]
    assert freshness["cache_source"] in {"cache", "recomputed"}
    if freshness["cache_source"] == "cache":
        assert isinstance(freshness.get("cache_age_seconds"), int)
    else:
        assert freshness.get("recompute_reason") in {"forced", "stale_or_miss"}


def test_citadel_overview_freshness_contract() -> None:
    client = TestClient(app)
    response = client.get(
        "/api/v1/citadel/overview",
        params={"owner_type": "user", "owner_id": 322, "force_refresh": True},
    )

    assert response.status_code == 200
    freshness = response.json()["data"]["freshness"]
    assert freshness["cache_source"] in {"cache", "recomputed"}
    assert "assessment_generated_at" in freshness
