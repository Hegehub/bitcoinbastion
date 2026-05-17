from app.services.citadel.citadel_assessment_service import CitadelAssessmentService
from app.services.citadel.inheritance_verification_service import InheritanceVerificationService
from app.services.script.descriptor_awareness_service import DescriptorAwarenessService
from app.services.script.script_analyzer_service import ScriptAnalyzerService


class RepairPlanService:
    @staticmethod
    def _item(
        *,
        priority: int,
        severity: str,
        title: str,
        description: str,
        dependency_area: str,
        expected_resilience_improvement: str,
        effort_estimate: str,
        evidence: list[str],
    ) -> dict[str, object]:
        return {
            "priority_score": max(0, min(100, priority)),
            "severity": severity,
            "title": title,
            "description": description,
            "dependency_area": dependency_area,
            "expected_resilience_improvement": expected_resilience_improvement,
            "effort_estimate": effort_estimate,
            "status": "open",
            "evidence_refs": evidence,
            "synthetic_component": True,
            "synthetic_reason": "Deterministic baseline model with partial synthetic assumptions.",
            "production_replacement_path": "Replace with production-grade telemetry, attestations, and provider-linked evidence.",
            "confidence_penalty": 0.15,
            "operator_warning": "Synthetic/baseline Citadel output: validate with real operational evidence before critical action.",
            "limitations": ["Output includes synthetic or baseline assumptions and is not full production attestation."],
            "source_quality": {"source_type": "synthetic", "is_fallback": True},
            "explainability": {
                "driven_by": evidence,
                "priority_inputs": {
                    "severity": severity,
                    "dependency_area": dependency_area,
                },
            },
        }

    def build(self, *, owner_id: int) -> dict[str, object]:
        assessment_service = CitadelAssessmentService()
        recovery = assessment_service.recovery_report(owner_id=owner_id)
        script_profile = ScriptAnalyzerService().analyze(script_hint="single-sig")
        descriptor_profile = DescriptorAwarenessService().evaluate(
            has_descriptor=False,
            has_recovery_instructions=False,
            has_backup_reference=False,
        )
        inheritance = InheritanceVerificationService().evaluate(
            owner_id=owner_id,
            recovery_readiness_score=recovery.recovery_readiness_score,
            has_instructions=not any("instructions" in warning.lower() for warning in recovery.warnings),
            human_dependency_score=recovery.human_dependency_score,
            descriptor_available=descriptor_profile.has_descriptor,
            artifact_completeness_score=float(recovery.artifact_summary.get("completeness_score", 0.0)),
            verification_freshness_score=max(
                0.0,
                1.0
                - (
                    float(recovery.artifact_summary.get("freshness", {}).get("stale_required_count", 0.0))
                    / max(1.0, float(recovery.artifact_summary.get("freshness", {}).get("artifact_count", 1.0)))
                ),
            ),
            emergency_contact_coverage=0.4,
            recovery_path_complexity=max(0.0, min(1.0, script_profile.complexity_score)),
            operational_readability_score=descriptor_profile.completeness_score,
        )

        items: list[dict[str, object]] = []
        if recovery.artifact_summary.get("missing_required_labels"):
            items.append(
                self._item(
                    priority=95,
                    severity="critical",
                    title="Verify missing required recovery artifacts",
                    description="Required recovery artifacts are missing verification and block deterministic recovery.",
                    dependency_area="recovery_artifacts",
                    expected_resilience_improvement="Increase deterministic recovery readiness and reduce custody loss risk.",
                    effort_estimate="4-8 hours",
                    evidence=list(recovery.artifact_summary.get("missing_required_labels", [])),
                )
            )
        if recovery.artifact_summary.get("stale_required_labels"):
            items.append(
                self._item(
                    priority=88,
                    severity="warning",
                    title="Refresh stale recovery verifications",
                    description="Re-verify stale artifacts and attach fresh evidence references.",
                    dependency_area="verification_freshness",
                    expected_resilience_improvement="Reduce stale-proof risk and improve recovery confidence.",
                    effort_estimate="2-6 hours",
                    evidence=list(recovery.artifact_summary.get("stale_required_labels", [])),
                )
            )

        for gap in inheritance.get("critical_gaps", []):
            area = "inheritance" if "inheritance" in gap.lower() else "descriptor" if "descriptor" in gap.lower() else "operations"
            items.append(
                self._item(
                    priority=82 if area == "inheritance" else 78,
                    severity="warning",
                    title="Close inheritance readiness gap",
                    description=str(gap),
                    dependency_area=area,
                    expected_resilience_improvement="Improve heir execution reliability under emergency conditions.",
                    effort_estimate="1-3 days",
                    evidence=[str(gap)],
                )
            )

        if recovery.human_dependency_score > 0.7:
            items.append(
                self._item(
                    priority=90,
                    severity="critical",
                    title="Reduce single-operator dependency",
                    description="Introduce backup operator path for recovery/inheritance workflows.",
                    dependency_area="human_dependency",
                    expected_resilience_improvement="Reduce operational fragility during stressed recovery events.",
                    effort_estimate="2-4 days",
                    evidence=[f"human_dependency_score={recovery.human_dependency_score}"],
                )
            )

        if descriptor_profile.completeness_score < 0.6:
            items.append(
                self._item(
                    priority=84,
                    severity="warning",
                    title="Strengthen descriptor readiness package",
                    description="Provide descriptor references, instructions, and backup metadata for heirs/operators.",
                    dependency_area="descriptor_readiness",
                    expected_resilience_improvement="Improve deterministic recovery handoff quality and reduce ambiguity.",
                    effort_estimate="1-2 days",
                    evidence=list(descriptor_profile.warnings),
                )
            )

        items.sort(key=lambda item: int(item["priority_score"]), reverse=True)

        return {
            "owner_id": owner_id,
            "items": items,
            "freshness": {"source": "citadel_repair_planner_v2"},
            "confidence": 0.78,
            "synthetic_component": True,
            "synthetic_reason": "Repair priorities are baseline heuristics derived from synthetic/baseline Citadel inputs.",
            "production_replacement_path": "Back with production incident telemetry and verified workflow outcomes.",
            "confidence_penalty": 0.15,
            "operator_warning": "Repair plan is advisory and synthetic-influenced; validate against live operations evidence.",
            "evidence_refs": ["citadel:repair_plan", "citadel:baseline_model"],
            "limitations": ["Heuristic prioritization may differ from production incident reality."],
            "source_quality": {"source_type": "synthetic", "is_fallback": True},
            "explainability": {
                "priority_logic": "derived from recovery artifacts, inheritance gaps, human dependency, descriptor readiness",
                "recovery_summary": recovery.artifact_summary,
                "inheritance_status": inheritance.get("status"),
                "inheritance_gaps": inheritance.get("critical_gaps", []),
                "descriptor_completeness_score": descriptor_profile.completeness_score,
            },
        }
