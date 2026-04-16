from datetime import UTC, datetime

from app.schemas.citadel import (
    CitadelAssessmentOut,
    CitadelFindingOut,
    RecoveryArtifactOut,
    RecoveryReadinessOut,
)
from app.services.citadel.recovery_artifact_service import RecoveryArtifactRecord
from app.services.citadel.recovery_readiness_engine import RecoveryReadinessEngine


class CitadelAssessmentService:
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

        recovery_score_100 = round(recovery.recovery_readiness_score * 100, 2)
        operational = 74.0 if recovery.recovery_readiness_score >= 0.7 else 58.0
        policy_maturity = 68.0 if recovery.recovery_readiness_score >= 0.7 else 55.0
        privacy = 71.0
        treasury = 66.0
        custody = 72.0
        vendor = 64.0
        inheritance = 62.0 if recovery.recovery_readiness_score >= 0.7 else 48.0
        fee_survivability = 69.0

        overall = round(
            (
                custody
                + recovery_score_100
                + privacy
                + treasury
                + vendor
                + inheritance
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
            inheritance_readiness_score=inheritance,
            fee_survivability_score=fee_survivability,
            policy_maturity_score=policy_maturity,
            operational_hygiene_score=operational,
            critical_findings=findings,
            warnings=[],
            recommendations=["Verify backup artifacts and refresh recovery drills quarterly."],
            explainability={
                "recovery": recovery.model_dump(),
                "scoring_weights": {
                    "uniform": True,
                    "domains": 9,
                },
            },
            freshness={"assessment_generated_at": now.isoformat()},
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
