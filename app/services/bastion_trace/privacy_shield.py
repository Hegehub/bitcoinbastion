from datetime import UTC, datetime

from app.schemas.bastion_trace import PrivacyBand, PrivacyShieldReport
from app.services.bastion_trace.address_reuse import AddressReuseService
from app.services.bastion_trace.consolidation_risk import ConsolidationRiskService
from app.services.bastion_trace.dust_radar import DustRadarService
from app.services.bastion_trace.privacy_guidance import build_privacy_guidance
from app.services.bastion_trace.toxic_change import ToxicChangeService
from app.services.bastion_trace.utxo_hygiene import UTXOHygieneService


class PrivacyShieldService:
    def build_privacy_shield(
        self, address: str, utxos: list[int] | None = None, reuse_count: int | None = None
    ) -> PrivacyShieldReport:
        hygiene = UTXOHygieneService().build(address, utxos)
        dust = DustRadarService().build(utxos)
        reuse = AddressReuseService().build(reuse_count)
        consolidation = ConsolidationRiskService().build(utxos)
        toxic = ToxicChangeService().build(False)
        if utxos is None:
            return PrivacyShieldReport(
                address=address,
                chain="bitcoin",
                privacy_exposure_score=0.0,
                privacy_band=PrivacyBand.UNKNOWN,
                utxo_hygiene=hygiene,
                dust_radar=dust,
                address_reuse=reuse,
                consolidation_risk=consolidation,
                toxic_change=toxic,
                privacy_reason_codes=[
                    "PRIVACY_SHIELD_CREATED",
                    "PRIVACY_DATA_SOURCE_LIMITED",
                    "PRIVACY_NOT_ILLICIT_RISK",
                ],
                privacy_limitations=["utxo_data_unavailable"],
                privacy_guidance=build_privacy_guidance(),
                evidence_refs=[],
                confidence=0.2,
                freshness="UNKNOWN",
                advisory_not_legal_verdict=True,
                not_consensus_proof=True,
                no_custody=True,
                created_at=datetime.now(UTC),
            )
        score = 0.0
        if reuse.reuse_detected:
            score += 25
        if dust.dust_exposure_detected:
            score += 15
        if consolidation.consolidation_risk_level.value == "HIGH":
            score += 20
        if toxic.possible_toxic_change_detected:
            score += 20
        band = (
            PrivacyBand.LOW
            if score < 25
            else (
                PrivacyBand.MEDIUM
                if score < 50
                else PrivacyBand.HIGH if score < 75 else PrivacyBand.CRITICAL
            )
        )
        return PrivacyShieldReport(
            address=address,
            chain="bitcoin",
            privacy_exposure_score=score,
            privacy_band=band,
            utxo_hygiene=hygiene,
            dust_radar=dust,
            address_reuse=reuse,
            consolidation_risk=consolidation,
            toxic_change=toxic,
            privacy_reason_codes=["PRIVACY_SHIELD_CREATED", "PRIVACY_NOT_ILLICIT_RISK"],
            privacy_limitations=[],
            privacy_guidance=build_privacy_guidance(),
            evidence_refs=[],
            confidence=0.4,
            freshness="UNKNOWN",
            advisory_not_legal_verdict=True,
            not_consensus_proof=True,
            no_custody=True,
            created_at=datetime.now(UTC),
        )
