from app.services.access.offline_pack_verifier import OfflinePackVerificationResult


def test_verification_result_is_not_an_access_token():
    result = OfflinePackVerificationResult(
        True, "allow_offline", "verified", restrictions=("not_bearer", "device_bound")
    )
    assert "not_bearer" in result.restrictions
