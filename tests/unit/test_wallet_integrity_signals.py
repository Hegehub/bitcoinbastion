from datetime import UTC, datetime

from app.domain.access.integrity import AccessIntegritySignalStatus
from app.services.wallet_auth.integrity_signals import collect_wallet_signals

NOW = datetime(2026, 7, 26, tzinfo=UTC)


def test_bip322_legacy_stale_and_hardware_metadata() -> None:
    recent = collect_wallet_signals(
        {"wallet_proof_method": "bip322", "wallet_proof_age_seconds": 60}, NOW
    )[0]
    legacy = collect_wallet_signals({"wallet_proof_method": "legacy_bitcoin_message"}, NOW)[0]
    stale = collect_wallet_signals(
        {"wallet_proof_method": "bip322", "wallet_proof_age_seconds": 700000}, NOW
    )[0]
    hardware = collect_wallet_signals(
        {"wallet_proof_method": "hardware_wallet", "wallet_proof_age_seconds": 60}, NOW
    )[0]
    assert recent.score_delta > legacy.score_delta > stale.score_delta
    assert (
        hardware.score_delta < hardware.maximum_points
        and hardware.evidence_code == "hardware_metadata_unverified"
    )


def test_network_mismatch_and_revoked_proof_are_unsafe() -> None:
    mismatch = collect_wallet_signals({"wallet_network_mismatch": True}, NOW)[0]
    revoked = collect_wallet_signals({"wallet_proof_revoked": True}, NOW)[0]
    assert mismatch.status is AccessIntegritySignalStatus.UNSAFE and mismatch.hard_cap == 29
    assert revoked.status is AccessIntegritySignalStatus.UNSAFE and revoked.hard_cap == 20
