from app.services.citadel.citadel_assessment_service import CitadelAssessmentService


def test_citadel_assessment_service_returns_assessment_with_explainability() -> None:
    out = CitadelAssessmentService().build_assessment(owner_type="user", owner_id=2)

    assert out.owner_id == 2
    assert 0 <= out.overall_score <= 100
    assert out.explainability


def test_citadel_recovery_report_returns_structured_payload() -> None:
    out = CitadelAssessmentService().recovery_report(owner_id=3)

    assert 0 <= out.recovery_readiness_score <= 1
    assert out.recoverability_assumption in {"strong", "moderate", "weak"}
    assert out.freshness
