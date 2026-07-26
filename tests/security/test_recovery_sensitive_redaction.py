from app.services.wallet_auth.recovery.redaction import safe_recovery_metadata


def test_safe_metadata_contains_commitments_only() -> None:
    metadata = safe_recovery_metadata(
        {"factor_fingerprint": "sha256:test", "reason_code": "verified"}
    )
    assert metadata == {"factor_fingerprint": "sha256:test", "reason_code": "verified"}
