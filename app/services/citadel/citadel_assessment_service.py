import json
from datetime import UTC, datetime

from app.core.config import get_settings
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
    DEFAULT_SCORE_WEIGHTS: dict[str, float] = {
        "custody_resilience_score": 0.16,
        "recovery_readiness_score": 0.18,
        "privacy_resilience_score": 0.1,
        "treasury_resilience_score": 0.1,
        "vendor_independence_score": 0.08,
        "inheritance_readiness_score": 0.12,
        "fee_survivability_score": 0.08,
        "policy_maturity_score": 0.08,
        "operational_hygiene_score": 0.1,
    }

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

    @staticmethod
    def _coverage_summary(*, explainability: dict[str, object], required_domains: list[str]) -> dict[str, object]:
        present = [domain for domain in required_domains if domain in explainability]
        missing = [domain for domain in required_domains if domain not in explainability]
        coverage = round(len(present) / len(required_domains), 3) if required_domains else 1.0
        return {
            "required_domains": required_domains,
            "present_domains": present,
            "missing_domains": missing,
            "coverage_score": coverage,
            "guarantee": "pass" if not missing else "partial",
        }

    def _score_weights(self) -> tuple[dict[str, float], str, str]:
        base = dict(self.DEFAULT_SCORE_WEIGHTS)
        raw = (get_settings().citadel_score_weights_json or "").strip()
        if not raw:
            return base, "citadel_v2_weighted", "default"
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            return base, "citadel_v2_weighted", "configured_invalid"
        if not isinstance(parsed, dict):
            return base, "citadel_v2_weighted", "configured_invalid"

        updated = False
        for key in base:
            value = parsed.get(key)
            if isinstance(value, (int, float)) and float(value) >= 0:
                base[key] = float(value)
                updated = True
        total = sum(base.values())
        if total <= 0:
            return dict(self.DEFAULT_SCORE_WEIGHTS), "citadel_v2_weighted", "configured_invalid"

        normalized = {key: round(value / total, 6) for key, value in base.items()}
        if not updated:
            return dict(self.DEFAULT_SCORE_WEIGHTS), "citadel_v2_weighted", "configured_invalid"
        return normalized, "citadel_v2_weighted_custom", "configured_valid"

    def _external_signal_factors(self) -> tuple[dict[str, float], str]:
        raw = (get_settings().citadel_external_signal_factors_json or "").strip()
        if not raw:
            return {}, "none"
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            return {}, "configured_invalid"
        if not isinstance(parsed, dict):
            return {}, "configured_invalid"
        factors: dict[str, float] = {}
        for key in self.DEFAULT_SCORE_WEIGHTS:
            value = parsed.get(key)
            if isinstance(value, (int, float)):
                factors[key] = max(0.5, min(1.5, float(value)))
        if not factors:
            return {}, "configured_invalid"
        return factors, "configured_valid"

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

        policy_maturity = self._clamp_percent(
            self._safe_float(policy.get("policy_maturity_score"), default=0.0)
        )
        privacy = self._clamp_percent(45.0 + (inheritance_score_100 * 0.35) + (policy_maturity * 0.2))
        treasury = self._clamp_percent(48.0 + (policy_maturity * 0.3) + (recovery_score_100 * 0.22))
        fee_survivability = self._clamp_percent(50.0 + (recovery_score_100 * 0.3) + (inheritance_score_100 * 0.2))
        operational = self._clamp_percent(35.0 + (recovery_score_100 * 0.45) + (policy_maturity * 0.2))

        weights, calibration_version, score_weight_source = self._score_weights()
        weighted_inputs = {
            "custody_resilience_score": custody,
            "recovery_readiness_score": recovery_score_100,
            "privacy_resilience_score": privacy,
            "treasury_resilience_score": treasury,
            "vendor_independence_score": vendor,
            "inheritance_readiness_score": inheritance_score_100,
            "fee_survivability_score": fee_survivability,
            "policy_maturity_score": policy_maturity,
            "operational_hygiene_score": operational,
        }
        external_factors, external_factor_source = self._external_signal_factors()
        adjusted_inputs = {
            key: self._clamp_percent(value * external_factors.get(key, 1.0))
            for key, value in weighted_inputs.items()
        }
        overall = round(sum(adjusted_inputs[key] * weight for key, weight in weights.items()), 2)

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
        if external_factor_source == "configured_invalid":
            warnings.append(
                CitadelFindingOut(
                    title="Calibration override ignored",
                    severity="warning",
                    domain="calibration",
                    detail="CITADEL_EXTERNAL_SIGNAL_FACTORS_JSON is set but invalid; defaults were used.",
                )
            )
        if score_weight_source == "configured_invalid":
            warnings.append(
                CitadelFindingOut(
                    title="Weight override ignored",
                    severity="warning",
                    domain="calibration",
                    detail="CITADEL_SCORE_WEIGHTS_JSON is set but invalid; defaults were used.",
                )
            )

        now = datetime.now(UTC)
        explainability_payload: dict[str, object] = {
            "recovery": recovery.model_dump(),
            "inheritance": inheritance,
            "policy": policy,
            "sovereignty_graph": {
                "spof_count": spof_count,
                "findings": graph.get("findings", []),
            },
            "scoring_weights": {
                "uniform": False,
                "weights": weights,
                "calibration_version": calibration_version,
            },
            "score_inputs": weighted_inputs,
            "score_inputs_adjusted": adjusted_inputs,
            "external_signal_factors": external_factors,
            "external_signal_factor_source": external_factor_source,
            "score_weight_source": score_weight_source,
        }
        explainability_payload["guarantees"] = self._coverage_summary(
            explainability=explainability_payload,
            required_domains=[
                "recovery",
                "inheritance",
                "policy",
                "sovereignty_graph",
                "score_inputs",
                "score_inputs_adjusted",
            ],
        )

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
            explainability=explainability_payload,
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
