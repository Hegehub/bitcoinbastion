from app.schemas.wallet import WalletHealthRequest, WalletHealthResponse


class WalletHealthService:
    def evaluate(self, payload: WalletHealthRequest) -> WalletHealthResponse:
        fragmentation = min(1.0, payload.utxo_count / 200)
        privacy = max(0.0, 1.0 - payload.largest_utxo_share)
        fee_exposure = min(1.0, payload.avg_fee_rate_sat_vb / 100)
        health = max(0.0, min(1.0, 1 - (0.4 * fragmentation + 0.3 * fee_exposure) + 0.3 * privacy))

        recommendations: list[str] = []
        if fragmentation > 0.6:
            recommendations.append("Consider UTXO consolidation during low fee periods.")
        if fee_exposure > 0.7:
            recommendations.append("Use batching and timing strategy to reduce fee exposure.")
        if privacy < 0.4:
            recommendations.append("Improve coin control and avoid address reuse.")

        return WalletHealthResponse(
            health_score=health,
            utxo_fragmentation_score=fragmentation,
            privacy_score=privacy,
            fee_exposure_score=fee_exposure,
            recommendations=recommendations,
        )
