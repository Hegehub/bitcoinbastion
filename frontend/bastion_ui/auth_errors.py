# ruff: noqa: E501
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FrontendAuthError:
    code: str
    message: str
    next_action: str | None = None


SAFE_AUTH_ERRORS: dict[str, FrontendAuthError] = {
    "wallet_challenge_expired": FrontendAuthError(
        "wallet_challenge_expired", "This wallet challenge has expired.", "generate_new_challenge"
    ),
    "wallet_proof_invalid": FrontendAuthError(
        "wallet_proof_invalid", "The wallet signature could not be verified.", "retry_wallet_proof"
    ),
    "lnurl_k1_expired": FrontendAuthError(
        "lnurl_k1_expired", "This Lightning wallet request has expired.", "generate_new_challenge"
    ),
    "lnurl_k1_reused": FrontendAuthError(
        "lnurl_k1_reused",
        "This Lightning wallet request was already used.",
        "generate_new_challenge",
    ),
    "lnurl_signature_invalid": FrontendAuthError(
        "lnurl_signature_invalid", "The Lightning wallet approval could not be verified."
    ),
    "unsupported_wallet": FrontendAuthError(
        "unsupported_wallet", "This wallet does not support the required proof method."
    ),
    "device_revoked": FrontendAuthError(
        "device_revoked", "This Bastion device has been revoked.", "bind_new_device"
    ),
    "principal_revoked": FrontendAuthError(
        "principal_revoked", "This wallet principal is revoked.", "recovery"
    ),
    "session_expired": FrontendAuthError(
        "session_expired", "Your Bastion access session has expired.", "reauthenticate"
    ),
    "step_up_required": FrontendAuthError(
        "step_up_required", "Additional wallet approval is required.", "step_up"
    ),
    "upgrade_required": FrontendAuthError(
        "upgrade_required", "This capability requires a different entitlement.", "view_plans"
    ),
    "metric_not_allowed": FrontendAuthError(
        "metric_not_allowed", "This metric is not available to the current entitlement."
    ),
    "quota_exceeded": FrontendAuthError(
        "quota_exceeded", "The backend usage quota has been reached."
    ),
    "payment_pending": FrontendAuthError(
        "payment_pending", "Payment settlement is still pending.", "verify_payment"
    ),
    "payment_expired": FrontendAuthError(
        "payment_expired", "This payment request has expired.", "create_payment"
    ),
    "payment_verification_failed": FrontendAuthError(
        "payment_verification_failed", "Bastion could not verify payment settlement."
    ),
    "withdraw_policy_denied": FrontendAuthError(
        "withdraw_policy_denied", "Backend policy did not approve this refund or payout."
    ),
    "recovery_required": FrontendAuthError(
        "recovery_required", "Recover Bastion access before continuing.", "recovery"
    ),
    "lockdown_active": FrontendAuthError(
        "lockdown_active", "Emergency Lockdown is active.", "recovery"
    ),
}


def safe_auth_error(code: str) -> FrontendAuthError:
    return SAFE_AUTH_ERRORS.get(
        code,
        FrontendAuthError(
            "authentication_error", "Bastion could not complete this authentication request."
        ),
    )
