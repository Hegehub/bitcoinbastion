from app.schemas.wallet import WalletHealthRequest
from app.services.wallet.health_service import WalletHealthService


def test_wallet_health_service_recommendations() -> None:
    payload = WalletHealthRequest(utxo_count=250, largest_utxo_share=0.8, avg_fee_rate_sat_vb=120)
    result = WalletHealthService().evaluate(payload)

    assert 0 <= result.health_score <= 1
    assert result.recommendations
