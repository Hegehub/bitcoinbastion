import json
from datetime import UTC, datetime
from dataclasses import dataclass

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
from app.services.mempool.fee_market_model import FeeMarketModel
from app.services.mempool.mempool_analyzer_service import MempoolAnalyzerService, MempoolSnapshot
from app.services.script.descriptor_awareness_service import DescriptorAwarenessService
from app.services.script.script_analyzer_service import ScriptAnalyzerService
from app.services.utxo.utxo_analyzer_service import UTXOAnalyzerService




@dataclass
class InputQualityMeta:
    source_type: str
    freshness: str
    confidence: float
    quality_classification: str
    note: str = ""

class CitadelAssessmentService:
    @dataclass
    class WalletRuntimeContext:
        wallet_type: str = "single-sig"
        descriptor_hint: str = ""
        fee_exposure_score: float = 0.5
        wallet_health_score: float | None = None
        utxo_values_sats: list[int] | None = None
        has_recent_health_report: bool = False,
        backup_verified: bool | None = None,
        recovery_instructions_verified: bool | None = None,
        descriptor_verified: bool | None = None,
        signer_count: int | None = None,
        artifact_verification_age_days: int | None = None

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
    def _coverage_summary(
        *, explainability: dict[str, object], required_domains: list[str]
    ) -> dict[str, object]:
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

    def _utxo_signal(self, *, context: "CitadelAssessmentService.WalletRuntimeContext") -> dict[str, object]:
        utxo_values = context.utxo_values_sats or []
        if not utxo_values:
            # Conservative fallback for missing runtime context.
            utxo_values = [1_000, 10_000, 100_000]
        analysis = UTXOAnalyzerService().analyze(utxo_values_sats=utxo_values)
        high_fee_projection = None
        for item in analysis.fee_projections:
            if item.scenario == "stress_high_fee":
                high_fee_projection = item
                break
        if high_fee_projection is None and analysis.fee_projections:
            high_fee_projection = analysis.fee_projections[-1]

        high_fee_score = 0.0
        if high_fee_projection is not None:
            high_fee_score = min(100.0, (high_fee_projection.estimated_fee_sats / 200_000) * 100)

        return {
            "analysis": analysis,
            "fragmentation_score_100": round(analysis.fragmentation_score * 100, 2),
            "dust_ratio_100": round(analysis.dust_ratio * 100, 2),
            "spend_complexity_score_100": round(
                min(100.0, (analysis.estimated_inputs_to_spend_1m_sats / 20) * 100),
                2,
            ),
            "high_fee_exposure_score_100": round(high_fee_score, 2),
        }

    @staticmethod
    def _mempool_signal(*, context: "CitadelAssessmentService.WalletRuntimeContext") -> dict[str, object]:
        fee_exposure = max(0.0, min(1.0, context.fee_exposure_score))
        backlog_scale = int(30_000 + fee_exposure * 120_000)
        snapshot = MempoolSnapshot(
            backlog_tx_count=backlog_scale,
            backlog_vbytes=backlog_scale * 900,
            median_fee_rate_sat_vb=8.0 + fee_exposure * 64.0,
            high_priority_fee_rate_sat_vb=20.0 + fee_exposure * 110.0,
        )
        state = MempoolAnalyzerService().analyze(snapshot)
        market = FeeMarketModel().estimate(mempool=state, target_blocks=3)
        return {"snapshot": snapshot, "state": state, "market": market}

    @staticmethod
    def _script_descriptor_signal(*, context: "CitadelAssessmentService.WalletRuntimeContext") -> dict[str, object]:
        hint = (context.descriptor_hint or context.wallet_type or "single-sig").strip()
        script = ScriptAnalyzerService().analyze(script_hint=hint)
        descriptor = DescriptorAwarenessService().evaluate(
            has_descriptor=bool(context.descriptor_hint),
            has_recovery_instructions=context.has_recent_health_report,
            has_backup_reference=context.has_recent_health_report,
        )
        return {"script": script, "descriptor": descriptor}


    @staticmethod
    def _quality_meta(*, source_type: str, freshness: str, confidence: float, note: str = "") -> dict[str, object]:
        source = source_type if source_type in {"real", "fallback", "synthetic", "unknown"} else "unknown"
        classification = {
            "real": "REAL",
            "fallback": "FALLBACK",
            "synthetic": "SYNTHETIC",
            "unknown": "UNKNOWN",
        }[source]
        return InputQualityMeta(
            source_type=source,
            freshness=freshness or "unknown",
            confidence=round(max(0.0, min(1.0, float(confidence))), 3),
            quality_classification=classification,
            note=note,
        ).__dict__

    def _input_quality_matrix(
        self,
        *,
        context: "CitadelAssessmentService.WalletRuntimeContext",
        recovery: RecoveryReadinessOut,
        inheritance: dict[str, object],
        policy: dict[str, object],
        graph: dict[str, object],
        utxo: dict[str, object],
        mempool: dict[str, object],
        script_descriptor: dict[str, object],
    ) -> dict[str, dict[str, object]]:
        return {
            "wallet_runtime_context": self._quality_meta(
                source_type="real" if context.has_recent_health_report else "fallback",
                freshness="runtime_session",
                confidence=0.8 if context.has_recent_health_report else 0.55,
                note="Derived from API/runtime-provided wallet context",
            ),
            "recovery": self._quality_meta(
                source_type="fallback" if not context.has_recent_health_report else "real",
                freshness=str(recovery.freshness.get("source", "unknown")),
                confidence=float(recovery.confidence),
                note="Recovery artifacts may be template-derived when evidence is missing",
            ),
            "inheritance": self._quality_meta(
                source_type="synthetic",
                freshness=str(inheritance.get("freshness", {}).get("source", "unknown")),
                confidence=float(inheritance.get("confidence", 0.0)),
                note="Current inheritance scoring includes owner-derived deterministic heuristics",
            ),
            "policy": self._quality_meta(
                source_type="real" if context.wallet_health_score is not None else "fallback",
                freshness=str(policy.get("freshness", {}).get("source", "unknown")),
                confidence=float(policy.get("confidence", 0.0)),
                note="Policy maturity uses runtime health score when available",
            ),
            "sovereignty_graph": self._quality_meta(
                source_type="real" if context.descriptor_hint else "fallback",
                freshness=str(graph.get("freshness", {}).get("source", "unknown")),
                confidence=float(graph.get("confidence", 0.0)),
                note="Topology is deterministic from wallet profile assumptions",
            ),
            "utxo": self._quality_meta(
                source_type="real" if context.utxo_values_sats else "fallback",
                freshness="runtime_session",
                confidence=0.82 if context.utxo_values_sats else 0.5,
                note="Uses fallback UTXO set when runtime values are absent",
            ),
            "mempool": self._quality_meta(
                source_type="synthetic",
                freshness=str(mempool["market"].freshness),
                confidence=float(mempool["market"].confidence),
                note="Mempool snapshot is synthesized from fee exposure context",
            ),
            "script": self._quality_meta(
                source_type="fallback" if not context.descriptor_hint else "real",
                freshness="runtime_session",
                confidence=0.8 if context.descriptor_hint else 0.58,
                note="Script risk inferred from descriptor hint or wallet type",
            ),
            "descriptor_awareness": self._quality_meta(
                source_type="fallback" if not context.descriptor_hint else "real",
                freshness="runtime_session",
                confidence=0.78 if context.descriptor_hint else 0.52,
                note="Completeness depends on descriptor and health-report proxies",
            ),
        }

    @staticmethod
    def build_wallet_context(
        *,
        wallet_type: str = "",
        descriptor_hint: str = "",
        fee_exposure_score: float | None = None,
        wallet_health_score: float | None = None,
        utxo_values_sats: list[int] | None = None,
        has_recent_health_report: bool = False,
        backup_verified: bool | None = None,
        recovery_instructions_verified: bool | None = None,
        descriptor_verified: bool | None = None,
        signer_count: int | None = None,
        artifact_verification_age_days: int | None = None,
    ) -> "CitadelAssessmentService.WalletRuntimeContext":
        return CitadelAssessmentService.WalletRuntimeContext(
            wallet_type=wallet_type or "single-sig",
            descriptor_hint=descriptor_hint or "",
            fee_exposure_score=max(0.0, min(1.0, float(fee_exposure_score or 0.5))),
            wallet_health_score=(
                None if wallet_health_score is None else max(0.0, min(1.0, float(wallet_health_score)))
            ),
            utxo_values_sats=utxo_values_sats or [],
            has_recent_health_report=has_recent_health_report,
            backup_verified=backup_verified,
            recovery_instructions_verified=recovery_instructions_verified,
            descriptor_verified=descriptor_verified,
            signer_count=signer_count,
            artifact_verification_age_days=artifact_verification_age_days,
        )

    def recovery_report(
        self,
        *,
        owner_id: int,
        wallet_context: "CitadelAssessmentService.WalletRuntimeContext | None" = None,
    ) -> RecoveryReadinessOut:
        context = wallet_context or self.build_wallet_context()
        has_descriptor = bool(context.descriptor_verified) if context.descriptor_verified is not None else bool(context.descriptor_hint)
        has_recent_health = context.has_recent_health_report
        script_profile = ScriptAnalyzerService().analyze(
            script_hint=context.descriptor_hint or context.wallet_type or "single-sig"
        )
        descriptor_profile = DescriptorAwarenessService().evaluate(
            has_descriptor=has_descriptor,
            has_recovery_instructions=has_recent_health,
            has_backup_reference=has_recent_health,
        )
        artifacts = [
            RecoveryArtifactRecord(
                artifact_type="descriptor",
                label=f"owner-{owner_id}-descriptor",
                is_verified=has_descriptor,
                required_for_recovery=True,
                verification_age_days=context.artifact_verification_age_days if context.artifact_verification_age_days is not None else (14 if has_recent_health else 180),
            ),
            RecoveryArtifactRecord(
                artifact_type="backup",
                label=f"owner-{owner_id}-backup",
                is_verified=(context.backup_verified if context.backup_verified is not None else has_recent_health),
                required_for_recovery=True,
                verification_age_days=context.artifact_verification_age_days if context.artifact_verification_age_days is not None else (30 if has_recent_health else 210),
            ),
            RecoveryArtifactRecord(
                artifact_type="instructions",
                label=f"owner-{owner_id}-runbook",
                is_verified=(context.backup_verified if context.backup_verified is not None else has_recent_health),
                required_for_recovery=False,
                verification_age_days=context.artifact_verification_age_days if context.artifact_verification_age_days is not None else (30 if has_recent_health else 180),
            ),
        ]
        wallet_type = (context.wallet_type or "").lower()
        if context.signer_count is not None:
            human_dependency_score = 0.35 if context.signer_count >= 3 else 0.55 if context.signer_count == 2 else 0.75
        elif "multi" in wallet_type:
            human_dependency_score = 0.45
        elif "watch" in wallet_type:
            human_dependency_score = 0.7
        else:
            human_dependency_score = 0.6
        raw = RecoveryReadinessEngine().evaluate(
            artifacts=artifacts,
            has_descriptor=has_descriptor,
            descriptor_completeness_score=descriptor_profile.completeness_score,
            has_instructions=has_recent_health and not descriptor_profile.warnings,
            human_dependency_score=human_dependency_score,
            script_risk_score=max(0.0, min(1.0, script_profile.complexity_score)),
        )
        return RecoveryReadinessOut.model_validate(raw)

    def build_assessment(
        self,
        *,
        owner_type: str,
        owner_id: int,
        wallet_context: "CitadelAssessmentService.WalletRuntimeContext | None" = None,
    ) -> CitadelAssessmentOut:
        context = wallet_context or self.build_wallet_context()
        recovery = self.recovery_report(owner_id=owner_id, wallet_context=context)
        inheritance = InheritanceVerificationService().evaluate(owner_id=owner_id)
        policy = CitadelPolicyService().evaluate(
            owner_id=owner_id,
            wallet_health_score=context.wallet_health_score,
            has_recent_health_report=context.has_recent_health_report,
        )
        graph = SovereigntyGraphService().build(
            owner_id=owner_id,
            wallet_type=context.wallet_type,
            has_descriptor=bool(context.descriptor_hint),
            has_recent_health_report=context.has_recent_health_report,
        )
        utxo = self._utxo_signal(context=context)
        mempool = self._mempool_signal(context=context)
        script_descriptor = self._script_descriptor_signal(context=context)

        spof_items = self._as_object_list(graph.get("single_points_of_failure", []))
        spof_count = len(spof_items)
        descriptor_completeness_score_100 = self._clamp_percent(
            script_descriptor["descriptor"].completeness_score * 100
        )
        descriptor_gap_penalty = max(0.0, (100.0 - descriptor_completeness_score_100) * 0.18)
        custody = self._clamp_percent(
            max(
                25.0,
                78.0
                - (spof_count * 12.0)
                - (utxo["fragmentation_score_100"] * 0.2)
                - descriptor_gap_penalty,
            )
        )
        vendor = self._clamp_percent(max(40.0, 72.0 - (spof_count * 8.0)))
        recovery_score_100 = self._clamp_percent(recovery.recovery_readiness_score * 100)
        inheritance_score_100 = self._clamp_percent(
            (self._safe_float(inheritance.get("completeness_score"), default=0.0) * 100)
            - ((100.0 - descriptor_completeness_score_100) * 0.22)
        )

        policy_maturity = self._clamp_percent(
            self._safe_float(policy.get("policy_maturity_score"), default=0.0)
        )
        privacy = self._clamp_percent(
            45.0
            + (inheritance_score_100 * 0.35)
            + (policy_maturity * 0.2)
            - (script_descriptor["script"].complexity_score * 12)
        )
        treasury = self._clamp_percent(48.0 + (policy_maturity * 0.3) + (recovery_score_100 * 0.22))
        fee_survivability = self._clamp_percent(
            50.0
            + (recovery_score_100 * 0.3)
            + (inheritance_score_100 * 0.2)
            - (utxo["high_fee_exposure_score_100"] * 0.25)
            - (utxo["spend_complexity_score_100"] * 0.15)
            - (min(100.0, mempool["market"].high_fee_scenario_sat_vb) * 0.15)
        )
        operational = self._clamp_percent(
            35.0
            + (recovery_score_100 * 0.45)
            + (policy_maturity * 0.2)
            + (script_descriptor["descriptor"].completeness_score * 10)
        )

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
        if utxo["fragmentation_score_100"] > 60:
            recommendations.append(
                "Prioritize UTXO consolidation window planning to reduce fragmentation drag."
            )
        if utxo["spend_complexity_score_100"] > 60:
            recommendations.append(
                "Reduce spend-path input complexity to improve high-fee survivability."
            )
        if spof_count > 0:
            recommendations.append(
                "Reduce signer concentration by adding independent signing path."
            )
        recommendations.extend(
            str(item)
            for item in self._as_object_list(inheritance.get("recommendations", []))
            if item
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
        if utxo["dust_ratio_100"] > 20:
            warnings.append(
                CitadelFindingOut(
                    title="Elevated UTXO dust ratio",
                    severity="warning",
                    domain="utxo",
                    detail="Dust-heavy UTXO distribution may reduce fee survivability during stress windows.",
                )
            )
        if utxo["spend_complexity_score_100"] > 70:
            warnings.append(
                CitadelFindingOut(
                    title="Elevated UTXO spend complexity",
                    severity="warning",
                    domain="utxo",
                    detail="High input-count dependency may degrade survivability under urgent spend conditions.",
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
        if script_descriptor["script"].risk_level == "high":
            warnings.append(
                CitadelFindingOut(
                    title="High script complexity risk",
                    severity="warning",
                    domain="script",
                    detail="Script profile indicates elevated operational fragility; verify signer flow.",
                )
            )
        if descriptor_completeness_score_100 < 60:
            warnings.append(
                CitadelFindingOut(
                    title="Descriptor completeness degraded",
                    severity="warning",
                    domain="descriptor",
                    detail="Descriptor readiness is below 60%; custody and inheritance resilience are penalized.",
                )
            )
        if descriptor_completeness_score_100 < 25:
            findings.append(
                CitadelFindingOut(
                    title="Descriptor readiness critical gap",
                    severity="critical",
                    domain="descriptor",
                    detail="Descriptor assumptions are weak; deterministic recovery guarantees are not met.",
                )
            )
        for item in script_descriptor["descriptor"].warnings:
            warnings.append(
                CitadelFindingOut(
                    title="Descriptor readiness gap",
                    severity="warning",
                    domain="descriptor",
                    detail=str(item),
                )
            )

        now = datetime.now(UTC)
        input_quality = self._input_quality_matrix(
            context=context,
            recovery=recovery,
            inheritance=inheritance,
            policy=policy,
            graph=graph,
            utxo=utxo,
            mempool=mempool,
            script_descriptor=script_descriptor,
        )

        explainability_payload: dict[str, object] = {
            "recovery": recovery.model_dump(),
            "inheritance": inheritance,
            "policy": policy,
            "sovereignty_graph": {
                "spof_count": spof_count,
                "findings": graph.get("findings", []),
            },
            "utxo": {
                "fragmentation_score_100": utxo["fragmentation_score_100"],
                "dust_ratio_100": utxo["dust_ratio_100"],
                "spend_complexity_score_100": utxo["spend_complexity_score_100"],
                "high_fee_exposure_score_100": utxo["high_fee_exposure_score_100"],
                "analysis": utxo["analysis"].model_dump(),
            },
            "mempool": {
                "congestion_state": mempool["state"].congestion_state,
                "suggested_fee_rate_sat_vb": mempool["market"].suggested_fee_rate_sat_vb,
                "high_fee_scenario_sat_vb": mempool["market"].high_fee_scenario_sat_vb,
                "confidence": mempool["market"].confidence,
                "freshness": mempool["market"].freshness,
                "explainability": mempool["market"].explainability,
            },
            "script": script_descriptor["script"].model_dump(),
                "descriptor_awareness": script_descriptor["descriptor"].model_dump(),
                "descriptor_completeness_score_100": descriptor_completeness_score_100,
                "descriptor_gap_penalty": round(descriptor_gap_penalty, 2),
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
            "calibration_input_quality": {
                "score": round(
                    (
                        (1.0 if score_weight_source == "configured_valid" else 0.5)
                        + (1.0 if external_factor_source == "configured_valid" else 0.5)
                    )
                    / 2,
                    3,
                ),
                "score_weight_source": score_weight_source,
                "external_signal_factor_source": external_factor_source,
            },
            "runtime_context": {
                "wallet_type": context.wallet_type,
                "has_descriptor_hint": bool(context.descriptor_hint),
                "has_recent_health_report": context.has_recent_health_report,
                "utxo_values_provided": bool(context.utxo_values_sats),
                "fee_exposure_score": context.fee_exposure_score,
                "backup_verified": context.backup_verified,
                "recovery_instructions_verified": context.recovery_instructions_verified,
                "descriptor_verified": context.descriptor_verified,
                "signer_count": context.signer_count,
                "artifact_verification_age_days": context.artifact_verification_age_days,
            },
            "input_quality": input_quality,
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
                "utxo",
                "mempool",
                "script",
                "descriptor_awareness",
                "input_quality",
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
                is_verified=False,
                required_for_recovery=True,
            ),
            RecoveryArtifactOut(
                artifact_type="backup",
                label=f"owner-{owner_id}-backup",
                is_verified=False,
                required_for_recovery=True,
            ),
        ]
