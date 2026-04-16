from app.schemas.privacy import PrivacyAssessmentRequest
from app.services.privacy.privacy_service import PrivacyRiskService


def test_privacy_risk_service_returns_explainable_high_risk_result() -> None:
    payload = PrivacyAssessmentRequest(
        reused_addresses=8,
        known_kyc_exposure=True,
        utxo_fragmentation_score=0.9,
        merged_clusters_count=4,
    )

    result = PrivacyRiskService().assess(payload)

    assert result.risk_level == "high"
    assert result.risk_score >= 70
    assert "reuse_component" in result.explainability
    assert result.priority_action
    assert any("Segregate KYC" in rec for rec in result.recommendations)


def test_privacy_risk_service_low_risk_path() -> None:
    payload = PrivacyAssessmentRequest(
        reused_addresses=0,
        known_kyc_exposure=False,
        utxo_fragmentation_score=0.1,
        merged_clusters_count=0,
    )

    result = PrivacyRiskService().assess(payload)

    assert result.risk_level == "low"
    assert result.risk_score < 35
    assert result.explainability["model"] == "privacy_risk_v1"
