from app.domain.utxo import FeeScenario, UTXOEntry
from app.schemas.utxo import UTXOAnalysisOut
from app.services.utxo.fee_exposure_service import FeeExposureService


class UTXOAnalyzerService:
    DUST_THRESHOLD_SATS = 1_000
    SMALL_OUTPUT_THRESHOLD_SATS = 50_000

    def __init__(self) -> None:
        self.fee_exposure = FeeExposureService()

    def analyze(self, *, utxo_values_sats: list[int], target_spend_sats: int = 1_000_000) -> UTXOAnalysisOut:
        entries = [UTXOEntry(value_sats=max(0, int(v))) for v in utxo_values_sats]
        utxo_count = len(entries)
        if utxo_count == 0:
            return UTXOAnalysisOut(
                utxo_count=0,
                dust_outputs=0,
                dust_ratio=0.0,
                fragmentation_score=1.0,
                estimated_inputs_to_spend_1m_sats=0,
                consolidation_candidate_count=0,
                liquidity_shortfall_sats=target_spend_sats,
                urgent_spend_feasible=False,
                high_fee_burden_ratio=0.0,
                consolidation_candidates_ranked=[],
                wallet_profile="empty",
                confidence=0.4,
                freshness={
                    "source": "wallet_snapshot",
                    "state": "missing",
                    "source_type": "fallback",
                    "provider_name": "unknown",
                    "is_mock": False,
                    "is_fallback": True,
                    "provider_count": 0,
                    "corroborated_by": [],
                    "conflicting_providers": [],
                    "confidence_adjustment": 0.2,
                    "freshness_band": "unknown",
                    "fallback_active": True,
                    "single_source_advisory": True,
                    "advisory_not_consensus_proof": True,
                    "operator_guidance": ["Collect provider-backed UTXO snapshot before critical decisions."],
                    "limitations": ["Fallback-only UTXO analysis."],
                },
                explainability={
                    "reason": "no_utxo_data",
                    "limitations": "Missing UTXO snapshot; analysis is fallback-only and low confidence.",
                },
                fee_projections=[],
            )

        values = sorted((entry.value_sats for entry in entries), reverse=True)
        total_balance = sum(values)
        dust_outputs = sum(1 for value in values if value <= self.DUST_THRESHOLD_SATS)
        dust_ratio = dust_outputs / utxo_count
        small_outputs = sum(1 for value in values if value < self.SMALL_OUTPUT_THRESHOLD_SATS)

        top_share = values[0] / max(1, total_balance)
        base_fragmentation = (small_outputs / utxo_count) * 0.55 + dust_ratio * 0.3
        concentration_penalty = 0.0 if top_share < 0.85 else min(0.15, (top_share - 0.85) * 0.8)
        fragmentation_score = min(1.0, base_fragmentation + concentration_penalty)

        accum = 0
        inputs = 0
        for value in values:
            accum += value
            inputs += 1
            if accum >= target_spend_sats:
                break

        urgent_feasible = accum >= target_spend_sats
        liquidity_shortfall = max(0, target_spend_sats - accum)

        current_fee = self.fee_exposure.estimate_projection(
            inputs=inputs,
            fee_scenario=FeeScenario(fee_rate_sat_vb=5.0, label="current"),
        )
        high_fee = self.fee_exposure.estimate_projection(
            inputs=inputs,
            fee_scenario=FeeScenario(fee_rate_sat_vb=80.0, label="stress_high_fee"),
        )
        emergency_fee = self.fee_exposure.estimate_projection(
            inputs=inputs,
            fee_scenario=FeeScenario(fee_rate_sat_vb=160.0, label="stress_emergency_fee"),
        )

        high_fee_burden = high_fee.estimated_fee_sats / max(1, target_spend_sats)

        ranked_candidates = sorted(
            [value for value in values if value < self.SMALL_OUTPUT_THRESHOLD_SATS],
            key=lambda v: (v > self.DUST_THRESHOLD_SATS, v),
        )[:12]

        if utxo_count == 1 and values[0] >= target_spend_sats:
            wallet_profile = "single_whale_utxo"
        elif dust_ratio >= 0.4:
            wallet_profile = "dust_heavy"
        elif small_outputs / utxo_count >= 0.65:
            wallet_profile = "many_small_utxos"
        elif fragmentation_score >= 0.45:
            wallet_profile = "fragmented"
        else:
            wallet_profile = "balanced"

        return UTXOAnalysisOut(
            utxo_count=utxo_count,
            dust_outputs=dust_outputs,
            dust_ratio=round(dust_ratio, 3),
            fragmentation_score=round(fragmentation_score, 3),
            estimated_inputs_to_spend_1m_sats=inputs,
            consolidation_candidate_count=small_outputs,
            liquidity_shortfall_sats=int(liquidity_shortfall),
            urgent_spend_feasible=urgent_feasible,
            high_fee_burden_ratio=round(high_fee_burden, 4),
            consolidation_candidates_ranked=ranked_candidates,
            wallet_profile=wallet_profile,
            confidence=0.75,
            freshness={
                "source": "wallet_snapshot",
                "utxo_count": utxo_count,
                "source_type": "runtime",
                "provider_name": "unknown",
                "is_mock": False,
                "is_fallback": False,
                "provider_count": 1,
                "corroborated_by": [],
                "conflicting_providers": [],
                "confidence_adjustment": 0.0,
                "freshness_band": "fresh",
                "fallback_active": False,
                "single_source_advisory": True,
                "advisory_not_consensus_proof": True,
                "operator_guidance": ["Corroborate UTXO set with an independent provider for high-impact actions."],
                "limitations": ["Caller-supplied UTXO set; not direct consensus attestation."],
            },
            explainability={
                "dust_threshold_sats": self.DUST_THRESHOLD_SATS,
                "small_output_threshold_sats": self.SMALL_OUTPUT_THRESHOLD_SATS,
                "target_spend_sats": target_spend_sats,
                "total_balance_sats": total_balance,
                "top_utxo_share": round(top_share, 4),
                "urgent_spend_feasible": urgent_feasible,
                "liquidity_shortfall_sats": int(liquidity_shortfall),
                "consolidation_rank_method": "dust_first_then_ascending_value",
                "source_quality": {
                    "source_type": "runtime",
                    "provider_name": "unknown",
                    "is_mock": False,
                    "is_fallback": False,
                    "limitations": "Analyzer evaluates caller-provided UTXO values; no direct provider attestation.",
                },
            },
            fee_projections=[current_fee, high_fee, emergency_fee],
        )
