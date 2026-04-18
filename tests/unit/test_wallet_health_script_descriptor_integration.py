from app.schemas.wallet import WalletHealthRequest
from app.services.wallet.health_service import WalletHealthService


def test_wallet_health_adds_script_descriptor_warnings() -> None:
    payload = WalletHealthRequest(
        utxo_count=3,
        largest_utxo_share=0.2,
        avg_fee_rate_sat_vb=5,
        script_hint="3QJmV3qfvL9SuYo34YihAf3sRCW3qSinyC",
        has_descriptor=False,
        has_recovery_instructions=False,
        has_backup_reference=False,
    )

    out = WalletHealthService().evaluate(payload)

    assert any("Descriptor reference missing" in item for item in out.recommendations)
    assert any("Script setup looks fragile" in item for item in out.recommendations)
