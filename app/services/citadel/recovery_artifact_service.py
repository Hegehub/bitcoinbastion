from pydantic import BaseModel


class RecoveryArtifactRecord(BaseModel):
    artifact_type: str
    label: str
    is_verified: bool
    required_for_recovery: bool
    verification_age_days: int | None = None
    max_allowed_age_days: int = 90


class RecoveryArtifactService:
    def summarize(self, *, artifacts: list[RecoveryArtifactRecord]) -> dict[str, object]:
        required = [a for a in artifacts if a.required_for_recovery]
        verified_required = [a for a in required if a.is_verified]
        stale_required = [
            a
            for a in verified_required
            if a.verification_age_days is not None and a.verification_age_days > a.max_allowed_age_days
        ]

        missing_required = [a.label for a in required if not a.is_verified]
        freshness_penalty = (len(stale_required) / len(required)) if required else 0.0
        completeness = len(verified_required) / len(required) if required else 0.0
        completeness = max(0.0, completeness - (freshness_penalty * 0.25))

        return {
            "required_count": len(required),
            "verified_required_count": len(verified_required),
            "missing_required_labels": missing_required,
            "stale_required_labels": [a.label for a in stale_required],
            "completeness_score": round(completeness, 3),
            "freshness": {
                "source": "artifact_registry",
                "artifact_count": len(artifacts),
                "stale_required_count": len(stale_required),
                "max_allowed_age_days": 90,
            },
            "confidence": 0.78,
        }
