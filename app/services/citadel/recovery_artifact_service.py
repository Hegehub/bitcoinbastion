from pydantic import BaseModel, Field


class RecoveryArtifactRecord(BaseModel):
    artifact_type: str
    label: str
    is_verified: bool
    required_for_recovery: bool
    verification_age_days: int | None = None
    max_allowed_age_days: int = 90
    source_type: str = "unknown"
    verification_status: str = "unverified"
    freshness_band: str = "unknown"
    confidence: float = 0.5
    provenance_notes: str = ""
    evidence_refs: list[str] = Field(default_factory=list)


class RecoveryArtifactService:
    @staticmethod
    def _freshness_band(*, verification_age_days: int | None, max_allowed_age_days: int) -> str:
        if verification_age_days is None:
            return "unknown"
        if verification_age_days <= max(1, max_allowed_age_days // 3):
            return "fresh"
        if verification_age_days <= max_allowed_age_days:
            return "aging"
        return "stale"

    @staticmethod
    def _normalized_status(*, is_verified: bool, freshness_band: str) -> str:
        if not is_verified:
            return "unverified"
        if freshness_band == "stale":
            return "stale"
        return "verified"

    def summarize(self, *, artifacts: list[RecoveryArtifactRecord]) -> dict[str, object]:
        normalized_artifacts: list[RecoveryArtifactRecord] = []
        for artifact in artifacts:
            freshness_band = (
                artifact.freshness_band
                if artifact.freshness_band != "unknown"
                else self._freshness_band(
                    verification_age_days=artifact.verification_age_days,
                    max_allowed_age_days=artifact.max_allowed_age_days,
                )
            )
            status = (
                artifact.verification_status
                if artifact.verification_status not in {"", "unknown", "unverified"}
                else self._normalized_status(is_verified=artifact.is_verified, freshness_band=freshness_band)
            )
            normalized_artifacts.append(
                artifact.model_copy(
                    update={
                        "freshness_band": freshness_band,
                        "verification_status": status,
                    }
                )
            )

        required = [a for a in normalized_artifacts if a.required_for_recovery]
        verified_required = [a for a in required if a.verification_status == "verified"]
        stale_required = [a for a in required if a.freshness_band == "stale"]

        missing_required = [a.label for a in required if a.verification_status != "verified"]
        freshness_penalty = (len(stale_required) / len(required)) if required else 0.0
        fallback_required = [a for a in required if a.source_type in {"fallback", "synthetic", "unknown"}]
        provenance_penalty = (len(fallback_required) / len(required)) * 0.2 if required else 0.0
        completeness = len(verified_required) / len(required) if required else 0.0
        completeness = max(0.0, completeness - (freshness_penalty * 0.25) - provenance_penalty)

        confidence = (
            sum(max(0.0, min(1.0, float(a.confidence))) for a in normalized_artifacts) / len(normalized_artifacts)
            if normalized_artifacts
            else 0.0
        )

        return {
            "required_count": len(required),
            "verified_required_count": len(verified_required),
            "missing_required_labels": missing_required,
            "stale_required_labels": [a.label for a in stale_required],
            "completeness_score": round(completeness, 3),
            "provenance": [
                {
                    "artifact_type": a.artifact_type,
                    "label": a.label,
                    "source_type": a.source_type,
                    "verification_status": a.verification_status,
                    "verification_age_days": a.verification_age_days,
                    "freshness_band": a.freshness_band,
                    "required_for_recovery": a.required_for_recovery,
                    "confidence": round(max(0.0, min(1.0, float(a.confidence))), 3),
                    "provenance_notes": a.provenance_notes,
                    "evidence_refs": list(a.evidence_refs),
                }
                for a in normalized_artifacts
            ],
            "freshness": {
                "source": "artifact_registry",
                "artifact_count": len(normalized_artifacts),
                "stale_required_count": len(stale_required),
                "max_allowed_age_days": 90,
            },
            "confidence": round(confidence, 3),
        }
