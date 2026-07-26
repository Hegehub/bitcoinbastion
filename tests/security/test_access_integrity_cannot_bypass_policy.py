from app.services.access.access_integrity import AccessIntegrityEngine
from app.domain.access.integrity import AccessIntegrityContext
import pytest


def test_score_is_advisory_not_token_or_private_material_processor() -> None:
    result = AccessIntegrityEngine().calculate(
        AccessIntegrityContext(
            "hmac:principal",
            "bitcoin_wallet_principal",
            {
                "wallet_proof_method": "bip322",
                "wallet_proof_age_seconds": 1,
                "device_status": "active",
                "session_status": "active",
                "policy_state": "current",
            },
        )
    )
    public = str(result)
    assert result.version == "2.0"
    assert not hasattr(result, "token") and not hasattr(result, "allowed")
    assert "seed" not in public and "private_key" not in public


def test_client_claimed_high_score_is_not_evidence() -> None:
    result = AccessIntegrityEngine().calculate(
        AccessIntegrityContext(
            "hmac:principal", "lightning_wallet_principal", {"client_supplied_score": 100}
        )
    )
    assert result.score < 30


def test_raw_private_material_is_rejected_before_scoring() -> None:
    with pytest.raises(ValueError, match="forbidden_integrity_evidence"):
        AccessIntegrityEngine().calculate(
            AccessIntegrityContext(
                "hmac:principal",
                "bitcoin_wallet_principal",
                {"bitcoin_seed": "not-real-secret-material"},
            )
        )
