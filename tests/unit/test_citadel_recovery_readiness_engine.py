from app.services.citadel.recovery_artifact_service import RecoveryArtifactRecord, RecoveryArtifactService
from app.services.citadel.recovery_readiness_engine import RecoveryReadinessEngine


def test_recovery_artifact_summary_counts_required_and_missing() -> None:
    artifacts = [
        RecoveryArtifactRecord(artifact_type="descriptor", label="primary descriptor", is_verified=True, required_for_recovery=True),
        RecoveryArtifactRecord(artifact_type="backup", label="metal backup", is_verified=False, required_for_recovery=True),
    ]

    out = RecoveryArtifactService().summarize(artifacts=artifacts)

    assert out["required_count"] == 2
    assert out["verified_required_count"] == 1
    assert out["missing_required_labels"] == ["metal backup"]


def test_recovery_readiness_engine_reports_warnings_for_missing_controls() -> None:
    artifacts = [
        RecoveryArtifactRecord(artifact_type="descriptor", label="descriptor", is_verified=False, required_for_recovery=True),
    ]

    out = RecoveryReadinessEngine().evaluate(
        artifacts=artifacts,
        has_descriptor=False,
        has_instructions=False,
        human_dependency_score=0.9,
    )

    assert out["recovery_readiness_score"] < 0.5
    assert out["recoverability_assumption"] == "weak"
    assert out["warnings"]
