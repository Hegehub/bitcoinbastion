from app.schemas.bastion_trace import DustRadarReport


class DustRadarService:
    def build(self, utxos: list[int] | None, threshold: int = 546) -> DustRadarReport:
        if utxos is None:
            return DustRadarReport(
                dust_exposure_detected=False,
                dust_like_utxo_count=0,
                dust_threshold_sats=threshold,
                dust_exposure_score=0.0,
                limitations=["utxo_data_unavailable"],
                reason_codes=["UTXO_DATA_UNAVAILABLE"],
            )
        count = len([u for u in utxos if u <= threshold])
        return DustRadarReport(
            dust_exposure_detected=count > 0,
            dust_like_utxo_count=count,
            dust_threshold_sats=threshold,
            dust_exposure_score=min(100.0, count * 20.0),
            limitations=[],
            reason_codes=["DUST_EXPOSURE_POSSIBLE" if count > 0 else "DUST_EXPOSURE_NOT_DETECTED"],
        )
