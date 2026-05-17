class InheritanceVerificationService:
    @staticmethod
    def _clamp_unit(value: float) -> float:
        return max(0.0, min(1.0, float(value)))

    def evaluate(
        self,
        *,
        owner_id: int,
        recovery_readiness_score: float | None = None,
        has_instructions: bool | None = None,
        human_dependency_score: float | None = None,
        descriptor_available: bool | None = None,
        artifact_completeness_score: float | None = None,
        verification_freshness_score: float | None = None,
        emergency_contact_coverage: float | None = None,
        recovery_path_complexity: float | None = None,
        operational_readability_score: float | None = None,
    ) -> dict[str, object]:
        recovery_score = self._clamp_unit(recovery_readiness_score if recovery_readiness_score is not None else 0.45)
        instructions_score = 1.0 if bool(has_instructions) else 0.35
        dependency_score = 1.0 - self._clamp_unit(human_dependency_score if human_dependency_score is not None else 0.75)
        descriptor_score = 1.0 if bool(descriptor_available) else 0.3
        artifact_score = self._clamp_unit(artifact_completeness_score if artifact_completeness_score is not None else 0.5)
        freshness_score = self._clamp_unit(verification_freshness_score if verification_freshness_score is not None else 0.35)
        emergency_score = self._clamp_unit(emergency_contact_coverage if emergency_contact_coverage is not None else 0.4)
        complexity_score = 1.0 - self._clamp_unit(recovery_path_complexity if recovery_path_complexity is not None else 0.7)
        readability_score = self._clamp_unit(operational_readability_score if operational_readability_score is not None else 0.45)

        completeness = round(
            self._clamp_unit(
                recovery_score * 0.22
                + instructions_score * 0.14
                + dependency_score * 0.12
                + descriptor_score * 0.1
                + artifact_score * 0.12
                + freshness_score * 0.08
                + emergency_score * 0.12
                + complexity_score * 0.05
                + readability_score * 0.05
            ),
            3,
        )

        critical_gaps: list[str] = []
        if instructions_score < 0.6:
            critical_gaps.append("Inheritance instructions are incomplete or not validated.")
        if dependency_score < 0.4:
            critical_gaps.append("Inheritance flow depends on too few operators.")
        if descriptor_score < 0.6:
            critical_gaps.append("Descriptor availability for heirs is missing or weak.")
        if artifact_score < 0.6:
            critical_gaps.append("Required recovery artifacts are not sufficiently verified.")
        if freshness_score < 0.5:
            critical_gaps.append("Inheritance verification freshness is stale.")
        if emergency_score < 0.5:
            critical_gaps.append("Emergency contact/operator coverage is insufficient.")
        if complexity_score < 0.4:
            critical_gaps.append("Recovery path complexity is too high for a stressed inheritance event.")
        if readability_score < 0.5:
            critical_gaps.append("Operational readability for heirs is low.")

        status = "strong" if completeness >= 0.75 and not critical_gaps else "moderate" if completeness >= 0.5 else "weak"

        recommendations: list[str] = []
        if instructions_score < 0.8:
            recommendations.append("Publish step-by-step inheritance runbook with tested execution checkpoints.")
        if dependency_score < 0.7:
            recommendations.append("Add backup operator path to reduce single-human inheritance dependency.")
        if descriptor_score < 0.8:
            recommendations.append("Provide verified descriptor package for heir-facing recovery procedures.")
        if freshness_score < 0.7:
            recommendations.append("Re-verify inheritance artifacts on a defined recurring cadence.")
        if emergency_score < 0.7:
            recommendations.append("Document emergency contact escalation and cross-check operator reachability.")
        if complexity_score < 0.7:
            recommendations.append("Simplify recovery path to reduce required manual coordination steps.")

        return {
            "owner_id": owner_id,
            "status": status,
            "completeness_score": completeness,
            "human_dependency_score": round(1.0 - dependency_score, 3),
            "operational_readability_score": round(readability_score, 3),
            "critical_gaps": critical_gaps,
            "recommendations": recommendations,
            "freshness": {"source": "inheritance_operational_model_v2"},
            "confidence": round(0.62 + (0.22 * min(1.0, artifact_score + freshness_score) / 2), 3),
            "synthetic_component": True,
            "synthetic_reason": "Deterministic baseline model with partial synthetic assumptions.",
            "production_replacement_path": "Replace with production-grade telemetry, attestations, and provider-linked evidence.",
            "confidence_penalty": 0.15,
            "operator_warning": "Synthetic/baseline Citadel output: validate with real operational evidence before critical action.",
            "evidence_refs": ["citadel:baseline_model"],
            "limitations": ["Output includes synthetic or baseline assumptions and is not full production attestation."],
            "source_quality": {"source_type": "synthetic", "is_fallback": True},
            "explainability": {
                "signals": [
                    "recovery readiness",
                    "instruction completeness",
                    "human dependency",
                    "descriptor availability",
                    "artifact availability",
                    "verification freshness",
                    "emergency coverage",
                    "recovery complexity",
                    "operational readability",
                ],
                "score_components": {
                    "recovery_score": recovery_score,
                    "instructions_score": instructions_score,
                    "dependency_score": dependency_score,
                    "descriptor_score": descriptor_score,
                    "artifact_score": artifact_score,
                    "freshness_score": freshness_score,
                    "emergency_score": emergency_score,
                    "complexity_score": complexity_score,
                    "readability_score": readability_score,
                },
            },
        }
