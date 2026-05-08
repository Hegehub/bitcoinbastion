from app.services.citadel.inheritance_verification_service import InheritanceVerificationService


def test_inheritance_verification_service_strong_setup() -> None:
    out = InheritanceVerificationService().evaluate(
        owner_id=10,
        recovery_readiness_score=0.92,
        has_instructions=True,
        human_dependency_score=0.2,
        descriptor_available=True,
        artifact_completeness_score=0.9,
        verification_freshness_score=0.9,
        emergency_contact_coverage=0.95,
        recovery_path_complexity=0.2,
        operational_readability_score=0.9,
    )

    assert out["status"] == "strong"
    assert out["completeness_score"] >= 0.75
    assert out["critical_gaps"] == []


def test_inheritance_verification_service_moderate_setup() -> None:
    out = InheritanceVerificationService().evaluate(
        owner_id=11,
        recovery_readiness_score=0.63,
        has_instructions=True,
        human_dependency_score=0.55,
        descriptor_available=True,
        artifact_completeness_score=0.65,
        verification_freshness_score=0.6,
        emergency_contact_coverage=0.55,
        recovery_path_complexity=0.5,
        operational_readability_score=0.62,
    )

    assert out["status"] in {"moderate", "strong"}
    assert 0.5 <= out["completeness_score"] <= 0.9


def test_inheritance_verification_service_weak_setup() -> None:
    out = InheritanceVerificationService().evaluate(
        owner_id=12,
        recovery_readiness_score=0.25,
        has_instructions=False,
        human_dependency_score=0.9,
        descriptor_available=False,
        artifact_completeness_score=0.2,
        verification_freshness_score=0.1,
        emergency_contact_coverage=0.2,
        recovery_path_complexity=0.9,
        operational_readability_score=0.2,
    )

    assert out["status"] == "weak"
    assert out["completeness_score"] < 0.5
    assert out["critical_gaps"]
