from app.services.citadel.citadel_assessment_service import CitadelAssessmentService


def test_citadel_assessment_service_returns_assessment_with_explainability() -> None:
    out = CitadelAssessmentService().build_assessment(owner_type="user", owner_id=2)
    explainability = out.explainability.model_dump()

    assert out.owner_id == 2
    assert 0 <= out.overall_score <= 100
    assert out.explainability
    assert explainability["scoring_weights"]["calibration_version"] == "citadel_v2_weighted"
    assert explainability["guarantees"]["coverage_score"] == 1.0
    assert explainability["calibration_input_quality"]["score"] >= 0.5


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
        lambda self, owner_id, **kwargs: {"completeness_score": 1.8},
    )
    monkeypatch.setattr(
        "app.services.citadel.citadel_assessment_service.CitadelPolicyService.evaluate",
        lambda self, owner_id, **kwargs: {"policy_maturity_score": 180.0},
    )
    monkeypatch.setattr(
        "app.services.citadel.citadel_assessment_service.SovereigntyGraphService.build",
        lambda self, owner_id, **kwargs: {"single_points_of_failure": [], "findings": []},
    )

    out = service.build_assessment(
        owner_type="user",
        owner_id=2,
        wallet_context=service.build_wallet_context(
            wallet_type="multisig-2of3",
            descriptor_hint="tr(sortedmulti(2,...))",
            wallet_health_score=0.8,
            has_recent_health_report=True,
        ),
    )

    assert out.inheritance_readiness_score == 100.0
    assert out.policy_maturity_score == 100.0


def test_citadel_assessment_handles_non_numeric_scores_and_conditional_recommendation(
    monkeypatch,
) -> None:
    service = CitadelAssessmentService()

    monkeypatch.setattr(
        "app.services.citadel.citadel_assessment_service.InheritanceVerificationService.evaluate",
        lambda self, owner_id, **kwargs: {
            "completeness_score": "not-a-number",
            "recommendations": ["Test rec"],
        },
    )
    monkeypatch.setattr(
        "app.services.citadel.citadel_assessment_service.CitadelPolicyService.evaluate",
        lambda self, owner_id, **kwargs: {
            "policy_maturity_score": None,
            "gaps": ["Missing simulation cadence"],
        },
    )
    monkeypatch.setattr(
        "app.services.citadel.citadel_assessment_service.SovereigntyGraphService.build",
        lambda self, owner_id, **kwargs: {"single_points_of_failure": [], "findings": []},
    )

    out = service.build_assessment(
        owner_type="user",
        owner_id=2,
        wallet_context=service.build_wallet_context(
            wallet_type="multisig-2of3",
            descriptor_hint="tr(sortedmulti(2,...))",
            wallet_health_score=0.8,
            has_recent_health_report=True,
        ),
    )

    assert out.inheritance_readiness_score == 0.0
    assert out.policy_maturity_score == 0.0
    assert (
        "Reduce signer concentration by adding independent signing path." not in out.recommendations
    )
    assert "Test rec" in out.recommendations
    assert any(w.domain == "policy" for w in out.warnings)


def test_citadel_assessment_uses_weighted_score_inputs(monkeypatch) -> None:
    service = CitadelAssessmentService()

    monkeypatch.setattr(
        "app.services.citadel.citadel_assessment_service.InheritanceVerificationService.evaluate",
        lambda self, owner_id, **kwargs: {"completeness_score": 1.0},
    )
    monkeypatch.setattr(
        "app.services.citadel.citadel_assessment_service.CitadelPolicyService.evaluate",
        lambda self, owner_id, **kwargs: {"policy_maturity_score": 100.0},
    )
    monkeypatch.setattr(
        "app.services.citadel.citadel_assessment_service.SovereigntyGraphService.build",
        lambda self, owner_id, **kwargs: {"single_points_of_failure": [], "findings": []},
    )

    out = service.build_assessment(
        owner_type="user",
        owner_id=2,
        wallet_context=service.build_wallet_context(
            wallet_type="multisig-2of3",
            descriptor_hint="tr(sortedmulti(2,...))",
            wallet_health_score=0.8,
            has_recent_health_report=True,
        ),
    )
    explainability = out.explainability.model_dump()
    weights = explainability["scoring_weights"]["weights"]
    score_inputs_adjusted = explainability["score_inputs_adjusted"]
    weighted_total = round(
        sum(score_inputs_adjusted[key] * weight for key, weight in weights.items()), 2
    )

    assert out.overall_score == weighted_total


def test_citadel_assessment_supports_custom_weight_override(monkeypatch) -> None:
    service = CitadelAssessmentService()

    class FakeSettings:
        citadel_score_weights_json = '{"custody_resilience_score": 3, "recovery_readiness_score": 1, "privacy_resilience_score": 0}'
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

    out = service.build_assessment(
        owner_type="user",
        owner_id=2,
        wallet_context=service.build_wallet_context(
            wallet_type="multisig-2of3",
            descriptor_hint="tr(sortedmulti(2,...))",
            wallet_health_score=0.8,
            has_recent_health_report=True,
        ),
    )
    explainability = out.explainability.model_dump()
    base = explainability["score_inputs"]["recovery_readiness_score"]
    adjusted = explainability["score_inputs_adjusted"]["recovery_readiness_score"]

    assert adjusted < base
    assert explainability["external_signal_factors"]["recovery_readiness_score"] == 0.5
    assert explainability["external_signal_factor_source"] == "configured_valid"
    assert explainability["calibration_input_quality"]["score"] >= 0.75


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


def test_citadel_assessment_includes_utxo_domain_in_explainability() -> None:
    out = CitadelAssessmentService().build_assessment(owner_type="user", owner_id=2)
    explainability = out.explainability.model_dump()

    assert "utxo" in explainability
    assert explainability["utxo"]["fragmentation_score_100"] >= 0
    assert explainability["utxo"]["spend_complexity_score_100"] >= 0
    assert "utxo" in explainability["guarantees"]["present_domains"]
    assert "mempool" in explainability
    assert explainability["mempool"]["high_fee_scenario_sat_vb"] >= explainability["mempool"]["suggested_fee_rate_sat_vb"]
    assert "script" in explainability
    assert "descriptor_awareness" in explainability
    assert "script" in explainability["guarantees"]["present_domains"]
    assert "descriptor_awareness" in explainability["guarantees"]["present_domains"]


def test_citadel_assessment_emits_descriptor_gap_warnings_for_incomplete_metadata() -> None:
    out = CitadelAssessmentService().build_assessment(owner_type="user", owner_id=15)
    assert any(item.domain == "descriptor" for item in out.warnings)


def test_descriptor_completeness_penalizes_custody_and_inheritance_scores() -> None:
    service = CitadelAssessmentService()
    with_descriptor = service.build_assessment(
        owner_type="user",
        owner_id=2,
        wallet_context=service.build_wallet_context(
            descriptor_hint="tr(sortedmulti(2,...))",
            descriptor_verified=True,
            has_recent_health_report=True,
        ),
    )
    without_descriptor = service.build_assessment(
        owner_type="user",
        owner_id=2,
        wallet_context=service.build_wallet_context(
            descriptor_hint="",
            descriptor_verified=False,
            has_recent_health_report=False,
        ),
    )

    assert with_descriptor.inheritance_readiness_score > without_descriptor.inheritance_readiness_score
    assert with_descriptor.recovery_readiness_score > without_descriptor.recovery_readiness_score
    assert any(item.domain == "descriptor" for item in without_descriptor.warnings)


def test_citadel_assessment_exposes_input_quality_classification() -> None:
    service = CitadelAssessmentService()
    out = service.build_assessment(owner_type="user", owner_id=2)
    explainability = out.explainability.model_dump()

    quality = explainability["input_quality"]
    assert quality["mempool"]["quality_classification"] == "SYNTHETIC"
    assert quality["utxo"]["quality_classification"] == "FALLBACK"
    assert quality["inheritance"]["quality_classification"] == "SYNTHETIC"
    assert quality["policy"]["quality_classification"] in {"REAL", "FALLBACK"}


def test_citadel_assessment_input_quality_marks_real_runtime_inputs() -> None:
    service = CitadelAssessmentService()
    out = service.build_assessment(
        owner_type="user",
        owner_id=2,
        wallet_context=service.build_wallet_context(
            wallet_type="multisig-2of3",
            descriptor_hint="tr(sortedmulti(2,...))",
            wallet_health_score=0.8,
            utxo_values_sats=[100_000, 250_000],
            has_recent_health_report=True,
        ),
    )
    explainability = out.explainability.model_dump()
    quality = explainability["input_quality"]

    assert quality["wallet_runtime_context"]["quality_classification"] == "REAL"
    assert quality["utxo"]["quality_classification"] == "REAL"
    assert quality["script"]["quality_classification"] == "REAL"
    assert quality["descriptor_awareness"]["quality_classification"] == "REAL"


def test_recovery_artifacts_do_not_fabricate_owner_based_verification() -> None:
    artifacts = CitadelAssessmentService().recovery_artifacts(owner_id=2)
    assert all(not item.is_verified for item in artifacts)


def test_recovery_report_uses_runtime_linked_artifact_flags() -> None:
    service = CitadelAssessmentService()
    context = service.build_wallet_context(
        descriptor_hint="wsh(sortedmulti(...))",
        descriptor_verified=True,
        backup_verified=False,
        recovery_instructions_verified=True,
        signer_count=3,
        artifact_verification_age_days=7,
        has_recent_health_report=True,
    )
    report = service.recovery_report(owner_id=10, wallet_context=context)
    summary = report.artifact_summary

    assert summary["verified_required_count"] == 1
    assert summary["missing_required_labels"] == ["owner-10-backup"]


def test_citadel_assessment_surfaces_chain_state_risk_contribution() -> None:
    service = CitadelAssessmentService()
    out = service.build_assessment(
        owner_type="user",
        owner_id=33,
        wallet_context=service.build_wallet_context(
            chain_tip_height=900_000,
            chain_observed_height=900_000,
            chain_headers_height=900_003,
            chain_data_source="repository_fallback",
        ),
    )
    explainability = out.explainability.model_dump()
    assert "chain_state" in explainability
    assert explainability["chain_state"]["reorg_risk_score"] >= 0
    assert any(item.domain == "chain_state" for item in out.warnings)


def test_citadel_assessment_exposes_protocol_input_quality_summary() -> None:
    out = CitadelAssessmentService().build_assessment(owner_type="user", owner_id=88)
    protocol_quality = out.explainability.model_dump()["protocol_input_quality"]
    assert 0.0 <= protocol_quality["confidence"] <= 1.0
    assert isinstance(protocol_quality["fallback_or_synthetic_domains"], list)
    assert "limitations" in protocol_quality


def test_citadel_evidence_chain_spans_protocol_to_recommendation() -> None:
    out = CitadelAssessmentService().build_assessment(owner_type="user", owner_id=121)
    chain = out.explainability.model_dump()["evidence_chain"]
    domains = [item["domain"] for item in chain]
    assert domains == ["protocol", "scoring", "policy", "citadel", "recommendation"]


def test_citadel_protocol_confidence_degrades_under_fallback_chain_state() -> None:
    service = CitadelAssessmentService()
    strong = service.build_assessment(owner_type="user", owner_id=150, wallet_context=service.build_wallet_context(chain_data_source="provider_probe", chain_provider_data_age_seconds=10, chain_tip_height=100, chain_observed_height=99, chain_headers_height=100))
    weak = service.build_assessment(owner_type="user", owner_id=151, wallet_context=service.build_wallet_context(chain_data_source="provider_fallback", chain_provider_data_age_seconds=1800, chain_tip_height=100, chain_observed_height=99, chain_headers_height=102))
    strong_q = strong.explainability.model_dump()["protocol_input_quality"]
    weak_q = weak.explainability.model_dump()["protocol_input_quality"]
    assert weak_q["confidence"] <= strong_q["confidence"]
    assert weak_q["raw_confidence"] >= weak_q["confidence"]


def test_citadel_assessment_generates_audit_packets() -> None:
    out = CitadelAssessmentService().build_assessment(owner_type="user", owner_id=211)
    packets = out.explainability.model_dump()["audit_packets"]
    assert isinstance(packets, list)
    assert packets
    assert all("evidence_refs" in p for p in packets)
