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


def test_citadel_assessment_includes_spof_finding_and_penalizes_scores() -> None:
    out = CitadelAssessmentService().build_assessment(owner_type="user", owner_id=2)

    assert out.explainability["sovereignty_graph"]["spof_count"] > 0
    assert any(f.domain == "sovereignty_graph" for f in out.critical_findings)
    assert out.custody_resilience_score < 78.0
    assert out.vendor_independence_score < 72.0


def test_citadel_assessment_clamps_inheritance_and_policy_scores(monkeypatch) -> None:
    service = CitadelAssessmentService()

    monkeypatch.setattr(
        "app.services.citadel.citadel_assessment_service.InheritanceVerificationService.evaluate",
        lambda self, owner_id: {"completeness_score": 1.8},
    )
    monkeypatch.setattr(
        "app.services.citadel.citadel_assessment_service.CitadelPolicyService.evaluate",
        lambda self, owner_id: {"policy_maturity_score": 180.0},
    )
    monkeypatch.setattr(
        "app.services.citadel.citadel_assessment_service.SovereigntyGraphService.build",
        lambda self, owner_id: {"single_points_of_failure": [], "findings": []},
    )

    out = service.build_assessment(owner_type="user", owner_id=2)

    assert out.inheritance_readiness_score == 100.0
    assert out.policy_maturity_score == 100.0


def test_citadel_assessment_handles_non_numeric_scores_and_conditional_recommendation(monkeypatch) -> None:
    service = CitadelAssessmentService()

    monkeypatch.setattr(
        "app.services.citadel.citadel_assessment_service.InheritanceVerificationService.evaluate",
        lambda self, owner_id: {"completeness_score": "not-a-number", "recommendations": ["Test rec"]},
    )
    monkeypatch.setattr(
        "app.services.citadel.citadel_assessment_service.CitadelPolicyService.evaluate",
        lambda self, owner_id: {"policy_maturity_score": None, "gaps": ["Missing simulation cadence"]},
    )
    monkeypatch.setattr(
        "app.services.citadel.citadel_assessment_service.SovereigntyGraphService.build",
        lambda self, owner_id: {"single_points_of_failure": [], "findings": []},
    )

    out = service.build_assessment(owner_type="user", owner_id=2)

    assert out.inheritance_readiness_score == 0.0
    assert out.policy_maturity_score == 0.0
    assert "Reduce signer concentration by adding independent signing path." not in out.recommendations
    assert "Test rec" in out.recommendations
    assert any(w.domain == "policy" for w in out.warnings)
