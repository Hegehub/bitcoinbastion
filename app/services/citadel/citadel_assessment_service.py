from datetime import UTC, datetime

from app.schemas.citadel import (
    CitadelAssessmentOut,
    CitadelFindingOut,
    CitadelFreshnessOut,
    RecoveryArtifactOut,
    RecoveryReadinessOut,
)
from app.services.citadel.inheritance_verification_service import InheritanceVerificationService
from app.services.citadel.policy_maturity_service import CitadelPolicyService
from app.services.citadel.recovery_artifact_service import RecoveryArtifactRecord
from app.services.citadel.recovery_readiness_engine import RecoveryReadinessEngine
from app.services.citadel.sovereignty_graph_service import SovereigntyGraphService


class CitadelAssessmentService:
    @staticmethod
    def _safe_float(value: object, *, default: float = 0.0) -> float:
        if isinstance(value, (int, float)):
            return float(value)
        try:
            return float(str(value))
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _clamp_percent(value: float, *, default: float = 0.0) -> float:
        normalized = value if isinstance(value, (int, float)) else default
        return round(max(0.0, min(100.0, float(normalized))), 2)

    @staticmethod
    def _as_object_list(value: object) -> list[object]:
        return value if isinstance(value, list) else []

    def recovery_report(self, *, owner_id: int) -> RecoveryReadinessOut:
        artifacts = [
            RecoveryArtifactRecord(
                artifact_type="descriptor",
                label=f"owner-{owner_id}-descriptor",
                is_verified=True,
                required_for_recovery=True,
            ),
            RecoveryArtifactRecord(
                artifact_type="backup",
                label=f"owner-{owner_id}-backup",
                is_verified=(owner_id % 2 == 0),
                required_for_recovery=True,
            ),
            RecoveryArtifactRecord(
                artifact_type="instructions",
                label=f"owner-{owner_id}-runbook",
                is_verified=(owner_id % 3 != 0),
                required_for_recovery=False,
            ),
        ]
        raw = RecoveryReadinessEngine().evaluate(
            artifacts=artifacts,
            has_descriptor=True,
            has_instructions=(owner_id % 3 != 0),
            human_dependency_score=0.4 if owner_id % 2 == 0 else 0.75,
        )
        return RecoveryReadinessOut.model_validate(raw)

    def build_assessment(self, *, owner_type: str, owner_id: int) -> CitadelAssessmentOut:
        recovery = self.recovery_report(owner_id=owner_id)
        inheritance = InheritanceVerificationService().evaluate(owner_id=owner_id)
        policy = CitadelPolicyService().evaluate(owner_id=owner_id)
        graph = SovereigntyGraphService().build(owner_id=owner_id)

        spof_items = self._as_object_list(graph.get("single_points_of_failure", []))
        spof_count = len(spof_items)
        custody = self._clamp_percent(max(35.0, 78.0 - (spof_count * 12.0)))
        vendor = self._clamp_percent(max(40.0, 72.0 - (spof_count * 8.0)))
        recovery_score_100 = self._clamp_percent(recovery.recovery_readiness_score * 100)
        inheritance_score_100 = self._clamp_percent(
            self._safe_float(inheritance.get("completeness_score"), default=0.0) * 100
        )

        privacy = 71.0
        treasury = 66.0
        fee_survivability = 69.0
        policy_maturity = self._clamp_percent(
            self._safe_float(policy.get("policy_maturity_score"), default=0.0)
        )
        operational = self._clamp_percent(74.0 if recovery.recovery_readiness_score >= 0.7 else 58.0)

        overall = round(
            (
                custody
                + recovery_score_100
                + privacy
                + treasury
                + vendor
                + inheritance_score_100
                + fee_survivability
                + policy_maturity
                + operational
            )
            / 9,
            2,
        )

        findings: list[CitadelFindingOut] = []
        if recovery.recovery_readiness_score < 0.7:
            findings.append(
                CitadelFindingOut(
                    title="Recovery path fragility",
                    severity="critical",
                    domain="recovery",
                    detail="Not all required recovery artifacts are verified.",
                )
            )
        if spof_count > 0:
            findings.append(
                CitadelFindingOut(
                    title="Single points of failure detected",
                    severity="warning",
                    domain="sovereignty_graph",
                    detail=f"Detected {spof_count} SPOF edge(s) in dependency graph.",
                )
            )

        recommendations = ["Verify backup artifacts and refresh recovery drills quarterly."]
        if spof_count > 0:
            recommendations.append("Reduce signer concentration by adding independent signing path.")
        recommendations.extend(
            str(item) for item in self._as_object_list(inheritance.get("recommendations", [])) if item
        )

        warnings: list[CitadelFindingOut] = []
        for gap in self._as_object_list(policy.get("gaps", [])):
            warnings.append(
                CitadelFindingOut(
                    title="Policy maturity gap",
                    severity="warning",
                    domain="policy",
                    detail=str(gap),
                )
            )

        now = datetime.now(UTC)
        return CitadelAssessmentOut(
            id=0,
            owner_type=owner_type,
            owner_id=owner_id,
            overall_score=overall,
            custody_resilience_score=custody,
            recovery_readiness_score=recovery_score_100,
            privacy_resilience_score=privacy,
            treasury_resilience_score=treasury,
            vendor_independence_score=vendor,
            inheritance_readiness_score=inheritance_score_100,
            fee_survivability_score=fee_survivability,
            policy_maturity_score=policy_maturity,
            operational_hygiene_score=operational,
            critical_findings=findings,
            warnings=warnings,
            recommendations=recommendations,
            explainability={
                "recovery": recovery.model_dump(),
                "inheritance": inheritance,
                "policy": policy,
                "sovereignty_graph": {
                    "spof_count": spof_count,
                    "findings": graph.get("findings", []),
                },
                "scoring_weights": {
                    "uniform": True,
                    "domains": 9,
                },
            },
            freshness=CitadelFreshnessOut(assessment_generated_at=now.isoformat()),
            generated_at=now,
            created_at=now,
            updated_at=now,
        )

    def recovery_artifacts(self, *, owner_id: int) -> list[RecoveryArtifactOut]:
        return [
            RecoveryArtifactOut(
                artifact_type="descriptor",
                label=f"owner-{owner_id}-descriptor",
                is_verified=True,
                required_for_recovery=True,
            ),
            RecoveryArtifactOut(
                artifact_type="backup",
                label=f"owner-{owner_id}-backup",
                is_verified=(owner_id % 2 == 0),
                required_for_recovery=True,
            ),
        ]
