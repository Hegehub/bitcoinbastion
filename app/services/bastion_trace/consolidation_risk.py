from app.schemas.bastion_trace import ConsolidationRiskReport, PrivacyRiskLevel


class ConsolidationRiskService:
    def build(self, utxos: list[int] | None) -> ConsolidationRiskReport:
        if not utxos:
            return ConsolidationRiskReport(consolidation_risk_level=PrivacyRiskLevel.UNKNOWN, input_count=0, utxo_count=0, small_utxo_ratio=0.0, reason_codes=["UTXO_DATA_UNAVAILABLE"], limitations=["utxo_data_unavailable"])
        utxo_count = len(utxos)
        small_ratio = len([u for u in utxos if u < 100_000]) / utxo_count
        level = PrivacyRiskLevel.HIGH if utxo_count > 20 or small_ratio > 0.7 else PrivacyRiskLevel.MEDIUM if utxo_count > 8 else PrivacyRiskLevel.LOW
        code = "CONSOLIDATION_RISK_HIGH" if level == PrivacyRiskLevel.HIGH else "CONSOLIDATION_RISK_MEDIUM" if level == PrivacyRiskLevel.MEDIUM else "CONSOLIDATION_RISK_LOW"
        return ConsolidationRiskReport(consolidation_risk_level=level, input_count=utxo_count, utxo_count=utxo_count, small_utxo_ratio=small_ratio, reason_codes=[code], limitations=[])
