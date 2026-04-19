from pydantic import BaseModel


class RecoveryArtifactRecord(BaseModel):
    artifact_type: str
    label: str
    is_verified: bool
    required_for_recovery: bool


class RecoveryArtifactService:
    def summarize(self, *, artifacts: list[RecoveryArtifactRecord]) -> dict[str, object]:
        required = [a for a in artifacts if a.required_for_recovery]
        verified_required = [a for a in required if a.is_verified]

        missing_required = [a.label for a in required if not a.is_verified]
        completeness = len(verified_required) / len(required) if required else 0.0

        return {
            "required_count": len(required),
            "verified_required_count": len(verified_required),
            "missing_required_labels": missing_required,
            "completeness_score": round(completeness, 3),
            "freshness": {"source": "artifact_registry", "artifact_count": len(artifacts)},
            "confidence": 0.78,
        }
