from bastion_ui.access_redaction import redact_sensitive_object
from bastion_ui.access_storage import (
    DEVICE_PRIVATE_KEY_STORAGE_ALLOWED,
    ONE_TIME_API_KEY_STORAGE_ALLOWED,
    RAW_LNURL_SIGNATURE_STORAGE_ALLOWED,
    RAW_WALLET_SIGNATURE_STORAGE_ALLOWED,
    RECOVERY_CAPSULE_MATERIAL_STORAGE_ALLOWED,
)


def test_sensitive_auth_material_is_not_persisted() -> None:
    assert not any(
        (
            RAW_WALLET_SIGNATURE_STORAGE_ALLOWED,
            RAW_LNURL_SIGNATURE_STORAGE_ALLOWED,
            DEVICE_PRIVATE_KEY_STORAGE_ALLOWED,
            RECOVERY_CAPSULE_MATERIAL_STORAGE_ALLOWED,
            ONE_TIME_API_KEY_STORAGE_ALLOWED,
        )
    )


def test_wallet_lnurl_and_recovery_values_are_redacted() -> None:
    raw = {
        "k1": "raw-k1",
        "lnurl_signature": "raw-sig",
        "device_private_key": "private",
        "recovery_material": "recovery",
        "preimage": "preimage",
    }
    assert set(redact_sensitive_object(raw).values()) == {"<redacted>"}
