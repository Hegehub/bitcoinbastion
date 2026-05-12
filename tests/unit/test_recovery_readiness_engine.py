from app.services.citadel.recovery_artifact_service import RecoveryArtifactRecord
from app.services.citadel.recovery_readiness_engine import RecoveryReadinessEngine


def test_recovery_readiness_engine_includes_provenance_and_fallback_warning() -> None:
    out = RecoveryReadinessEngine().evaluate(
        artifacts=[
            RecoveryArtifactRecord(
                artifact_type="descriptor",
                label="descriptor",
                is_verified=True,
                required_for_recovery=True,
                verification_age_days=7,
                source_type="fallback",
                confidence=0.5,
            ),
            RecoveryArtifactRecord(
                artifact_type="backup",
                label="backup",
                is_verified=False,
                required_for_recovery=True,
                source_type="unknown",
                confidence=0.2,
            ),
        ],
        has_descriptor=True,
        has_instructions=False,
        human_dependency_score=0.8,
        script_risk_score=0.2,
    )

    assert out["artifact_summary"]["provenance"]
    assert any("fallback/synthetic" in warning for warning in out["warnings"])
    assert out["recovery_readiness_score"] < 0.8
