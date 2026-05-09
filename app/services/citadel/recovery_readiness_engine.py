from app.services.citadel.recovery_artifact_service import RecoveryArtifactRecord, RecoveryArtifactService


class RecoveryReadinessEngine:
    @staticmethod
    def _score_from_summary(value: object) -> float:
        if isinstance(value, (int, float)):
            return float(value)
        return 0.0

    def evaluate(
        self,
        *,
        artifacts: list[RecoveryArtifactRecord],
        has_descriptor: bool,
        descriptor_completeness_score: float | None = None,
        has_instructions: bool,
        human_dependency_score: float,
        script_risk_score: float = 0.0,
    ) -> dict[str, object]:
        artifact_summary = RecoveryArtifactService().summarize(artifacts=artifacts)
        descriptor_score = (
            max(0.0, min(1.0, float(descriptor_completeness_score)))
            if descriptor_completeness_score is not None
            else (1.0 if has_descriptor else 0.0)
        )

        score = self._score_from_summary(artifact_summary.get("completeness_score")) * 0.5
        score += descriptor_score * 0.25
        score += 0.15 if has_instructions else 0.0
        score += max(0.0, (1 - human_dependency_score)) * 0.1
        score -= max(0.0, min(1.0, script_risk_score)) * 0.1
        score = round(min(1.0, max(0.0, score)), 3)

        warnings: list[str] = []
        if not has_descriptor:
            warnings.append("Descriptor metadata missing; deterministic recovery path cannot be verified.")
        elif descriptor_score < 0.6:
            warnings.append("Descriptor completeness is degraded; recovery path assumptions are partially trusted.")
        if not has_instructions:
            warnings.append("Recovery instructions missing; inheritance/operator risk is elevated.")
        if human_dependency_score > 0.7:
            warnings.append("High human dependency detected; recovery is operationally fragile.")
        if script_risk_score > 0.7:
            warnings.append("High script complexity risk detected; recovery path requires additional validation.")
        if artifact_summary["missing_required_labels"]:
            warnings.append("Required recovery artifacts are not verified.")
        if artifact_summary.get("stale_required_labels"):
            warnings.append("Some required recovery artifacts are stale and require reverification.")
        fallback_required = [
            item
            for item in artifact_summary.get("provenance", [])
            if item.get("required_for_recovery") and item.get("source_type") in {"fallback", "synthetic", "unknown"}
        ]
        if fallback_required:
            warnings.append("Recovery readiness includes fallback/synthetic required artifacts; confidence is reduced.")

        return {
            "recovery_readiness_score": score,
            "artifact_summary": artifact_summary,
            "human_dependency_score": human_dependency_score,
            "warnings": warnings,
            "recoverability_assumption": "strong" if score >= 0.8 else "moderate" if score >= 0.5 else "weak",
            "freshness": artifact_summary["freshness"],
            "confidence": 0.76,
            "explainability": {
                "weights": {
                    "artifacts": 0.5,
                    "descriptor": 0.25,
                    "instructions": 0.15,
                    "human_dependency": 0.1,
                "script_risk": -0.1,
                },
                "artifact_summary": artifact_summary,
                "script_risk_score": script_risk_score,
                "descriptor_completeness_score": round(descriptor_score, 3),
                "artifact_provenance": artifact_summary.get("provenance", []),
            },
        }
