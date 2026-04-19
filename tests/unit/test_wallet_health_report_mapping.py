from datetime import UTC, datetime
from types import SimpleNamespace

from app.services.wallet.health_service import WalletHealthService


def test_wallet_health_report_mapping_parses_recommendations_json() -> None:
    report = SimpleNamespace(
        id=10,
        wallet_profile_id=4,
        health_score=0.71,
        utxo_fragmentation_score=0.4,
        privacy_score=0.6,
        fee_exposure_score=0.5,
        recommendations_json='["A", "B"]',
        generated_at=datetime.now(UTC),
    )

    out = WalletHealthService().to_report_out(report)

    assert out.id == 10
    assert out.wallet_profile_id == 4
    assert out.recommendations == ["A", "B"]


def test_wallet_health_report_mapping_handles_invalid_json() -> None:
    report = SimpleNamespace(
        id=11,
        wallet_profile_id=5,
        health_score=0.5,
        utxo_fragmentation_score=0.5,
        privacy_score=0.5,
        fee_exposure_score=0.5,
        recommendations_json='{"unexpected": true}',
        generated_at=datetime.now(UTC),
    )

    out = WalletHealthService().to_report_out(report)

    assert out.recommendations == []
