from app.services.wallet_auth.lnurl_recovery_factor import (
    RECOVERY_PUBLIC_ERROR,
    RECOVERY_PUBLIC_MESSAGE,
)


def test_public_recovery_messages_do_not_enumerate_internal_state() -> None:
    combined = f"{RECOVERY_PUBLIC_MESSAGE} {RECOVERY_PUBLIC_ERROR}".lower()
    for forbidden in (
        "principal exists",
        "subscription exists",
        "workspace exists",
        "key mismatch",
    ):
        assert forbidden not in combined
