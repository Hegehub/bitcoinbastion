from app.schemas.bastion_trace import PrivacyBand, PrivacyRiskLevel, UTXOHygieneReport


class UTXOHygieneService:
    def build(self, address: str, utxos: list[int] | None) -> UTXOHygieneReport:
        if not utxos:
            return UTXOHygieneReport(
                hygiene_score=0.0,
                hygiene_band=PrivacyBand.UNKNOWN,
                utxo_count=0,
                small_utxo_count=0,
                large_utxo_count=0,
                dust_like_utxo_count=0,
                reuse_detected=False,
                consolidation_risk_level=PrivacyRiskLevel.UNKNOWN,
                toxic_change_risk_level=PrivacyRiskLevel.UNKNOWN,
                limitations=["utxo_data_unavailable"],
                reason_codes=["UTXO_DATA_UNAVAILABLE", "UTXO_HYGIENE_BASELINE"],
            )
        utxo_count = len(utxos)
        small = len([v for v in utxos if v < 100_000])
        large = len([v for v in utxos if v >= 1_000_000])
        dust = len([v for v in utxos if v <= 546])
        score = min(100.0, (small / utxo_count) * 50 + (dust / utxo_count) * 50)
        band = PrivacyBand.LOW if score < 25 else PrivacyBand.MEDIUM if score < 50 else PrivacyBand.HIGH if score < 75 else PrivacyBand.CRITICAL
        cons = PrivacyRiskLevel.HIGH if utxo_count >= 20 else PrivacyRiskLevel.MEDIUM if utxo_count >= 8 else PrivacyRiskLevel.LOW
        return UTXOHygieneReport(
            hygiene_score=score,
            hygiene_band=band,
            utxo_count=utxo_count,
            small_utxo_count=small,
            large_utxo_count=large,
            dust_like_utxo_count=dust,
            reuse_detected=False,
            consolidation_risk_level=cons,
            toxic_change_risk_level=PrivacyRiskLevel.UNKNOWN,
            limitations=[],
            reason_codes=["UTXO_HYGIENE_BASELINE"],
        )
