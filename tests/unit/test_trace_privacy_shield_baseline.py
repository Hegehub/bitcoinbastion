from app.services.bastion_trace.dust_radar import DustRadarService
from app.services.bastion_trace.privacy_shield import PrivacyShieldService


def test_dust_threshold_default() -> None:
    r = DustRadarService().build([100, 546, 1000])
    assert r.dust_threshold_sats == 546
    assert r.dust_exposure_detected is True


def test_privacy_shield_unknown_without_utxo() -> None:
    r = PrivacyShieldService().build_privacy_shield("1BoatSLRHtKNngkdXEeobR76b53LETtpyT", None, None)
    assert r.privacy_band.value == "UNKNOWN"
    assert "PRIVACY_NOT_ILLICIT_RISK" in r.privacy_reason_codes
