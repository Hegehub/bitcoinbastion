from app.schemas.wallet import WalletHealthRequest
from app.services.wallet.health_service import WalletHealthService


def test_wallet_health_uses_utxo_analysis_when_values_provided() -> None:
    payload = WalletHealthRequest(
        utxo_count=5,
        largest_utxo_share=0.5,
        avg_fee_rate_sat_vb=12,
        utxo_values_sats=[700, 900, 2000, 10000, 1_200_000],
    )

    out = WalletHealthService().evaluate(payload)

    assert 0 <= out.health_score <= 1
    assert out.utxo_fragmentation_score > 0
    assert out.recommendations


def test_wallet_health_explainability_embeds_utxo_analysis() -> None:
    payload = WalletHealthRequest(
        utxo_count=4,
        largest_utxo_share=0.45,
        avg_fee_rate_sat_vb=18,
        utxo_values_sats=[900, 1_500, 22_000, 1_100_000],
    )

    out = WalletHealthService().evaluate(payload)

    explainability = out.explainability.model_dump()
    assert explainability["utxo_analysis"]["utxo_count"] == 4
    assert "utxo_analyzer" in explainability["data_sources"]
    assert out.confidence >= 0.8
    assert "spend_complexity" in explainability["score_components"]
