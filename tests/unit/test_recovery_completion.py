from app.services.wallet_auth.recovery.models import RecoveryCompletionResult, RecoveryCapsuleStatus


def test_completion_boundary_is_recovery_limited() -> None:
    result = RecoveryCompletionResult(
        "hmac:capsule",
        RecoveryCapsuleStatus.COMPLETED,
        "recovery_only",
        ("wallet_session", "child_api_key"),
        True,
    )
    assert result.session_mode == "recovery_only" and result.requires_fresh_step_up
