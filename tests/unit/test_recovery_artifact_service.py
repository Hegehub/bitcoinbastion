from app.services.citadel.recovery_artifact_service import (
    RecoveryArtifactRecord,
    RecoveryArtifactService,
)


def test_recovery_artifact_service_summarizes_verified_and_missing_required() -> None:
    summary = RecoveryArtifactService().summarize(
        artifacts=[
            RecoveryArtifactRecord(
                artifact_type="descriptor",
                label="descriptor-main",
                is_verified=True,
                required_for_recovery=True,
                verification_age_days=10,
                source_type="persisted",
                confidence=0.95,
                provenance_notes="verified against signed export",
                evidence_refs=["doc://descriptor-main-v3"],
            ),
            RecoveryArtifactRecord(
                artifact_type="backup",
                label="backup-main",
                is_verified=False,
                required_for_recovery=True,
                verification_age_days=120,
                source_type="runtime",
                confidence=0.6,
            ),
        ]
    )

    assert summary["required_count"] == 2
    assert summary["verified_required_count"] == 1
    assert "backup-main" in summary["missing_required_labels"]
    assert summary["provenance"][0]["verification_status"] == "verified"


def test_recovery_artifact_service_penalizes_fallback_and_stale_artifacts() -> None:
    summary = RecoveryArtifactService().summarize(
        artifacts=[
            RecoveryArtifactRecord(
                artifact_type="descriptor",
                label="descriptor-fallback",
                is_verified=True,
                required_for_recovery=True,
                verification_age_days=140,
                source_type="fallback",
                confidence=0.4,
            ),
            RecoveryArtifactRecord(
                artifact_type="backup",
                label="backup-fallback",
                is_verified=True,
                required_for_recovery=True,
                verification_age_days=150,
                source_type="synthetic",
                confidence=0.3,
            ),
        ]
    )

    assert summary["completeness_score"] < 0.8
    assert len(summary["stale_required_labels"]) == 2
    assert summary["confidence"] <= 0.4
