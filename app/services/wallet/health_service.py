import json
from datetime import UTC, datetime
from typing import cast

from app.db.models.wallet import WalletHealthReport
from app.schemas.wallet import WalletHealthReportOut, WalletHealthRequest, WalletHealthResponse
from app.schemas.common import ExplainabilityOut, FreshnessOut
from app.services.script.descriptor_awareness_service import DescriptorAwarenessService
from app.services.script.script_analyzer_service import ScriptAnalyzerService
from app.services.utxo.utxo_analyzer_service import UTXOAnalyzerService


class WalletHealthService:
    def evaluate(self, payload: WalletHealthRequest) -> WalletHealthResponse:
        utxo_analysis = None
        data_sources = ["wallet_input"]
        if payload.utxo_values_sats:
            utxo_analysis = UTXOAnalyzerService().analyze(utxo_values_sats=payload.utxo_values_sats)
            data_sources.append("utxo_analyzer")

        fragmentation = (
            utxo_analysis.fragmentation_score
            if utxo_analysis
            else min(1.0, payload.utxo_count / 200)
        )
        privacy = max(0.0, 1.0 - payload.largest_utxo_share)
        fee_exposure = min(1.0, payload.avg_fee_rate_sat_vb / 100)

        if utxo_analysis and utxo_analysis.fee_projections:
            high_fee_projection = next(
                (p for p in utxo_analysis.fee_projections if p.scenario == "stress_high_fee"),
                utxo_analysis.fee_projections[-1],
            )
            fee_exposure = min(1.0, high_fee_projection.estimated_fee_sats / 200_000)
        spend_complexity = 0.0
        if utxo_analysis is not None:
            spend_complexity = min(1.0, utxo_analysis.estimated_inputs_to_spend_1m_sats / 20)

        health = max(
            0.0,
            min(
                1.0,
                1
                - (0.35 * fragmentation + 0.25 * fee_exposure + 0.15 * spend_complexity)
                + 0.25 * privacy,
            ),
        )

        recommendations: list[str] = []
        if fragmentation > 0.6:
            recommendations.append("Consider UTXO consolidation during low fee periods.")
        if fee_exposure > 0.7:
            recommendations.append("Use batching and timing strategy to reduce fee exposure.")
        if privacy < 0.4:
            recommendations.append("Improve coin control and avoid address reuse.")
        if utxo_analysis and utxo_analysis.dust_ratio > 0.2:
            recommendations.append(
                "Dust outputs detected; prioritize cleanup transactions in low-fee windows."
            )
        if spend_complexity > 0.6:
            recommendations.append(
                "High spend complexity detected; reduce input count concentration before urgent spends."
            )

        if payload.script_hint:
            script = ScriptAnalyzerService().analyze(script_hint=payload.script_hint)
            data_sources.append("script_analyzer")
            if script.risk_level == "high":
                recommendations.append(
                    "Script setup looks fragile; validate script path and signer operations."
                )

        if payload.has_descriptor is not None:
            descriptor = DescriptorAwarenessService().evaluate(
                has_descriptor=bool(payload.has_descriptor),
                has_recovery_instructions=bool(payload.has_recovery_instructions),
                has_backup_reference=bool(payload.has_backup_reference),
            )
            data_sources.append("descriptor_awareness")
            recommendations.extend(descriptor.warnings)

        explainability = {
            "explanation": "Wallet health combines UTXO fragmentation, fee survivability, and privacy posture.",
            "confidence": 0.82 if utxo_analysis is not None else 0.66,
            "data_sources": data_sources,
            "score_components": {
                "fragmentation": round(fragmentation, 4),
                "fee_exposure": round(fee_exposure, 4),
                "spend_complexity": round(spend_complexity, 4),
                "privacy": round(privacy, 4),
            },
            "weights": {
                "fragmentation": 0.35,
                "fee_exposure": 0.25,
                "spend_complexity": 0.15,
                "privacy": 0.25,
            },
            "utxo_analysis": (
                utxo_analysis.model_dump()
                if utxo_analysis is not None
                else {"state": "not_provided"}
            ),
        }

        confidence = cast(float, explainability["confidence"])

        return WalletHealthResponse(
            health_score=health,
            utxo_fragmentation_score=fragmentation,
            privacy_score=privacy,
            fee_exposure_score=fee_exposure,
            recommendations=recommendations,
            confidence=confidence,
            explainability=ExplainabilityOut.model_validate(explainability),
            freshness=FreshnessOut.model_validate(
                {
                    "computed_at": datetime.now(UTC).isoformat(),
                    "ttl_seconds": 300,
                    "is_stale": False,
                }
            ),
        )

    def to_report_out(self, report: WalletHealthReport) -> WalletHealthReportOut:
        recommendations: list[str] = []
        try:
            parsed = json.loads(report.recommendations_json)
            if isinstance(parsed, list):
                recommendations = [str(item) for item in parsed]
        except json.JSONDecodeError:
            recommendations = []

        return WalletHealthReportOut(
            id=report.id,
            wallet_profile_id=report.wallet_profile_id,
            health_score=report.health_score,
            utxo_fragmentation_score=report.utxo_fragmentation_score,
            privacy_score=report.privacy_score,
            fee_exposure_score=report.fee_exposure_score,
            recommendations=recommendations,
            generated_at=report.generated_at,
        )
