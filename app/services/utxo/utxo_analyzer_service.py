from app.domain.utxo import FeeScenario, UTXOEntry
from app.schemas.utxo import UTXOAnalysisOut
from app.services.utxo.fee_exposure_service import FeeExposureService


class UTXOAnalyzerService:
    DUST_THRESHOLD_SATS = 1_000

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
                confidence=0.4,
                freshness={"source": "wallet_snapshot", "state": "missing"},
                explainability={"reason": "no_utxo_data"},
                fee_projections=[],
            )

        values = sorted((entry.value_sats for entry in entries), reverse=True)
        dust_outputs = sum(1 for value in values if value <= self.DUST_THRESHOLD_SATS)
        dust_ratio = dust_outputs / utxo_count
        small_outputs = sum(1 for value in values if value < 50_000)
        fragmentation_score = min(1.0, (small_outputs / utxo_count) * 0.7 + dust_ratio * 0.3)

        accum = 0
        inputs = 0
        for value in values:
            accum += value
            inputs += 1
            if accum >= target_spend_sats:
                break

        low_fee = self.fee_exposure.estimate_projection(
            inputs=inputs,
            fee_scenario=FeeScenario(fee_rate_sat_vb=5.0, label="current"),
        )
        high_fee = self.fee_exposure.estimate_projection(
            inputs=inputs,
            fee_scenario=FeeScenario(fee_rate_sat_vb=80.0, label="stress_high_fee"),
        )

        return UTXOAnalysisOut(
            utxo_count=utxo_count,
            dust_outputs=dust_outputs,
            dust_ratio=round(dust_ratio, 3),
            fragmentation_score=round(fragmentation_score, 3),
            estimated_inputs_to_spend_1m_sats=inputs,
            consolidation_candidate_count=small_outputs,
            confidence=0.75,
            freshness={"source": "wallet_snapshot", "utxo_count": utxo_count},
            explainability={
                "dust_threshold_sats": self.DUST_THRESHOLD_SATS,
                "small_output_threshold_sats": 50_000,
                "target_spend_sats": target_spend_sats,
            },
            fee_projections=[low_fee, high_fee],
        )
