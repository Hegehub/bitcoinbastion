from app.services.citadel.recovery_artifact_service import (
    RecoveryArtifactRecord,
    RecoveryArtifactService,
)


class RecoveryReadinessEngine:
    @staticmethod
    def _as_int(value: object, default: int = 0) -> int:
        if isinstance(value, bool):
            return default
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            return int(value)
        if isinstance(value, str) and value.strip().lstrip("-").isdigit():
            return int(value)
        return default

    @staticmethod
    def _as_str_list(value: object) -> list[str]:
        if not isinstance(value, list):
            return []
        return [str(item) for item in value]

    @staticmethod
    def _score_from_summary(value: object) -> float:
        if isinstance(value, (int, float)):
            return float(value)
        return 0.0

    @staticmethod
    def _build_recovery_slo(
        *, artifact_summary: dict[str, object], readiness_score: float, confidence: float
    ) -> dict[str, object]:
        required_count = RecoveryReadinessEngine._as_int(
            artifact_summary.get("required_count", 0), 0
        )
        verified_required = RecoveryReadinessEngine._as_int(
            artifact_summary.get("verified_required_count", 0), 0
        )
        stale_required_labels = RecoveryReadinessEngine._as_str_list(
            artifact_summary.get("stale_required_labels", [])
        )
        missing_required_labels = RecoveryReadinessEngine._as_str_list(
            artifact_summary.get("missing_required_labels", [])
        )

        stale_verification = len(stale_required_labels) > 0
        overdue_recovery_validation = len(missing_required_labels) > 0
        degraded_recovery_confidence = confidence < 0.7 or readiness_score < 0.65
        unresolved_critical_findings = len(stale_required_labels) + len(missing_required_labels)

        if unresolved_critical_findings >= 3 or (
            stale_verification and overdue_recovery_validation
        ):
            status = "critical"
        elif stale_verification or overdue_recovery_validation or degraded_recovery_confidence:
            status = "degraded"
        else:
            status = "healthy"

        return {
            "status": status,
            "target": {
                "required_artifacts_verified": "all",
                "required_artifacts_stale": "none",
                "minimum_confidence": 0.7,
            },
            "actual": {
                "required_artifacts": required_count,
                "verified_required_artifacts": verified_required,
                "stale_required_artifacts": len(stale_required_labels),
                "recovery_readiness_score": round(readiness_score, 3),
                "confidence": round(confidence, 3),
            },
            "signals": {
                "stale_verification": stale_verification,
                "overdue_recovery_validation": overdue_recovery_validation,
                "degraded_recovery_confidence": degraded_recovery_confidence,
                "unresolved_critical_findings": unresolved_critical_findings,
            },
            "synthetic_component": True,
            "synthetic_reason": "Deterministic baseline model with partial synthetic assumptions.",
            "production_replacement_path": "Replace with production-grade telemetry, attestations, and provider-linked evidence.",
            "confidence_penalty": 0.15,
            "operator_warning": "Synthetic/baseline Citadel output: validate with real operational evidence before critical action.",
            "evidence_refs": ["citadel:baseline_model"],
            "limitations": [
                "Output includes synthetic or baseline assumptions and is not full production attestation."
            ],
            "source_quality": {"source_type": "synthetic", "is_fallback": True},
            "explainability": {
                "stale_required_labels": stale_required_labels,
                "missing_required_labels": missing_required_labels,
                "conservative_semantics": True,
            },
        }

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
            warnings.append(
                "Descriptor metadata missing; deterministic recovery path cannot be verified."
            )
        elif descriptor_score < 0.6:
            warnings.append(
                "Descriptor completeness is degraded; recovery path assumptions are partially trusted."
            )
        if not has_instructions:
            warnings.append("Recovery instructions missing; inheritance/operator risk is elevated.")
        if human_dependency_score > 0.7:
            warnings.append("High human dependency detected; recovery is operationally fragile.")
        if script_risk_score > 0.7:
            warnings.append(
                "High script complexity risk detected; recovery path requires additional validation."
            )
        if RecoveryReadinessEngine._as_str_list(
            artifact_summary.get("missing_required_labels", [])
        ):
            warnings.append("Required recovery artifacts are not verified.")
        if artifact_summary.get("stale_required_labels"):
            warnings.append(
                "Some required recovery artifacts are stale and require reverification."
            )
        provenance = artifact_summary.get("provenance", [])
        provenance_items = provenance if isinstance(provenance, list) else []
        fallback_required = [
            item
            for item in provenance_items
            if isinstance(item, dict)
            and item.get("required_for_recovery")
            and item.get("source_type") in {"fallback", "synthetic", "unknown"}
        ]
        if fallback_required:
            warnings.append(
                "Recovery readiness includes fallback/synthetic required artifacts; confidence is reduced."
            )

        confidence = self._score_from_summary(artifact_summary.get("confidence", 0.0))
        recovery_slo = self._build_recovery_slo(
            artifact_summary=artifact_summary,
            readiness_score=score,
            confidence=confidence,
        )

        return {
            "recovery_readiness_score": score,
            "artifact_summary": artifact_summary,
            "human_dependency_score": human_dependency_score,
            "warnings": warnings,
            "recoverability_assumption": (
                "strong" if score >= 0.8 else "moderate" if score >= 0.5 else "weak"
            ),
            "freshness": artifact_summary["freshness"],
            "confidence": confidence,
            "synthetic_component": True,
            "synthetic_reason": "Recovery readiness uses baseline artifact/descriptor/human-dependency heuristic model.",
            "production_replacement_path": "Integrate real drill outcomes and signed recovery attestations.",
            "confidence_penalty": 0.15,
            "operator_warning": "Recovery readiness score includes synthetic assumptions; require drill evidence for critical decisions.",
            "evidence_refs": ["citadel:recovery_readiness", "artifact_registry"],
            "limitations": [
                "Heuristic scoring is conservative and not a guaranteed recovery proof."
            ],
            "source_quality": {"source_type": "synthetic", "is_fallback": True},
            "recovery_slo": recovery_slo,
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
                "recovery_slo": recovery_slo,
            },
        }
