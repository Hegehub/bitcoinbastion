from app.services.citadel.inheritance_verification_service import InheritanceVerificationService


def test_inheritance_verification_service_outputs_structured_status() -> None:
    out = InheritanceVerificationService().evaluate(owner_id=7)

    assert out["status"] in {"strong", "moderate", "weak"}
    assert 0 <= out["completeness_score"] <= 1
    assert 0 <= out["human_dependency_score"] <= 1
    assert out["recommendations"]
