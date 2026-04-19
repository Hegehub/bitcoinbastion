from app.services.citadel.citadel_assessment_service import CitadelAssessmentService


def test_citadel_assessment_service_returns_assessment_with_explainability() -> None:
    out = CitadelAssessmentService().build_assessment(owner_type="user", owner_id=2)
    explainability = out.explainability.model_dump()

    assert out.owner_id == 2
    assert 0 <= out.overall_score <= 100
    assert out.explainability
    assert explainability["scoring_weights"]["calibration_version"] == "citadel_v2_weighted"
    assert explainability["guarantees"]["coverage_score"] == 1.0


def test_citadel_recovery_report_returns_structured_payload() -> None:
    out = CitadelAssessmentService().recovery_report(owner_id=3)

    assert 0 <= out.recovery_readiness_score <= 1
    assert out.recoverability_assumption in {"strong", "moderate", "weak"}
    assert out.freshness


def test_citadel_assessment_includes_spof_finding_and_penalizes_scores() -> None:
    out = CitadelAssessmentService().build_assessment(owner_type="user", owner_id=2)
    explainability = out.explainability.model_dump()

    assert explainability["sovereignty_graph"]["spof_count"] > 0
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


def test_citadel_assessment_uses_weighted_score_inputs(monkeypatch) -> None:
    service = CitadelAssessmentService()

    monkeypatch.setattr(
        "app.services.citadel.citadel_assessment_service.InheritanceVerificationService.evaluate",
        lambda self, owner_id: {"completeness_score": 1.0},
    )
    monkeypatch.setattr(
        "app.services.citadel.citadel_assessment_service.CitadelPolicyService.evaluate",
        lambda self, owner_id: {"policy_maturity_score": 100.0},
    )
    monkeypatch.setattr(
        "app.services.citadel.citadel_assessment_service.SovereigntyGraphService.build",
        lambda self, owner_id: {"single_points_of_failure": [], "findings": []},
    )

    out = service.build_assessment(owner_type="user", owner_id=2)
    explainability = out.explainability.model_dump()
    weights = explainability["scoring_weights"]["weights"]
    score_inputs_adjusted = explainability["score_inputs_adjusted"]
    weighted_total = round(sum(score_inputs_adjusted[key] * weight for key, weight in weights.items()), 2)

    assert out.overall_score == weighted_total


def test_citadel_assessment_supports_custom_weight_override(monkeypatch) -> None:
    service = CitadelAssessmentService()

    class FakeSettings:
        citadel_score_weights_json = (
            '{"custody_resilience_score": 3, "recovery_readiness_score": 1, "privacy_resilience_score": 0}'
        )
        citadel_external_signal_factors_json = ""

    monkeypatch.setattr(
        "app.services.citadel.citadel_assessment_service.get_settings",
        lambda: FakeSettings(),
    )

    out = service.build_assessment(owner_type="user", owner_id=2)
    explainability = out.explainability.model_dump()
    assert explainability["scoring_weights"]["calibration_version"] == "citadel_v2_weighted_custom"
    assert explainability["score_weight_source"] == "configured_valid"
    assert abs(sum(explainability["scoring_weights"]["weights"].values()) - 1.0) < 1e-6


def test_citadel_assessment_applies_external_signal_factors(monkeypatch) -> None:
    service = CitadelAssessmentService()

    class FakeSettings:
        citadel_score_weights_json = ""
        citadel_external_signal_factors_json = (
            '{"recovery_readiness_score": 0.5, "operational_hygiene_score": 0.7}'
        )

    monkeypatch.setattr(
        "app.services.citadel.citadel_assessment_service.get_settings",
        lambda: FakeSettings(),
    )

    out = service.build_assessment(owner_type="user", owner_id=2)
    explainability = out.explainability.model_dump()
    base = explainability["score_inputs"]["recovery_readiness_score"]
    adjusted = explainability["score_inputs_adjusted"]["recovery_readiness_score"]

    assert adjusted < base
    assert explainability["external_signal_factors"]["recovery_readiness_score"] == 0.5
    assert explainability["external_signal_factor_source"] == "configured_valid"


def test_citadel_assessment_warns_on_invalid_external_factors(monkeypatch) -> None:
    service = CitadelAssessmentService()

    class FakeSettings:
        citadel_score_weights_json = ""
        citadel_external_signal_factors_json = '{"broken": "not-a-number"}'

    monkeypatch.setattr(
        "app.services.citadel.citadel_assessment_service.get_settings",
        lambda: FakeSettings(),
    )

    out = service.build_assessment(owner_type="user", owner_id=2)
    explainability = out.explainability.model_dump()
    assert explainability["external_signal_factor_source"] == "configured_invalid"
    assert any(item.domain == "calibration" for item in out.warnings)


def test_citadel_assessment_warns_on_invalid_weight_overrides(monkeypatch) -> None:
    service = CitadelAssessmentService()

    class FakeSettings:
        citadel_score_weights_json = '{"broken": "not-a-number"}'
        citadel_external_signal_factors_json = ""

    monkeypatch.setattr(
        "app.services.citadel.citadel_assessment_service.get_settings",
        lambda: FakeSettings(),
    )

    out = service.build_assessment(owner_type="user", owner_id=2)
    explainability = out.explainability.model_dump()
    assert explainability["score_weight_source"] == "configured_invalid"
    assert any("Weight override ignored" == item.title for item in out.warnings)
