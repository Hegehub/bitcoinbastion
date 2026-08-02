"""Bounded label vocabulary for Wallet/LNURL Prometheus telemetry."""

from enum import StrEnum


class ActorTypeLabel(StrEnum):
    BITCOIN_WALLET_PRINCIPAL = "bitcoin_wallet_principal"
    LIGHTNING_WALLET_PRINCIPAL = "lightning_wallet_principal"
    WALLET_DEVICE = "wallet_device"
    ACCESS_CERTIFICATE = "access_certificate"
    CHILD_API_KEY = "child_api_key"
    DELEGATED_PASS = "delegated_pass"
    BUSINESS_ROLE = "business_role"
    PAYREGISTER_DEVICE = "payregister_device"
    BOT = "bot"
    UNKNOWN = "unknown"


class AuthMethodLabel(StrEnum):
    BIP322 = "bip322"
    LEGACY_MESSAGE_SIGNATURE = "legacy_message_signature"
    HARDWARE_WALLET = "hardware_wallet"
    AIR_GAPPED = "air_gapped"
    MULTISIG_QUORUM = "multisig_quorum"
    LNURL_AUTH = "lnurl_auth"
    ACCESS_CERTIFICATE = "access_certificate"
    RECOVERY_CAPSULE = "recovery_capsule"
    UNKNOWN = "unknown"


class ResultLabel(StrEnum):
    SUCCESS = "success"
    FAILED = "failed"
    REJECTED = "rejected"
    EXPIRED = "expired"
    REVOKED = "revoked"
    DENIED = "denied"
    PENDING = "pending"
    SETTLED = "settled"
    CANCELLED = "cancelled"


class ReasonCodeLabel(StrEnum):
    INVALID_SIGNATURE = "invalid_signature"
    CHALLENGE_EXPIRED = "challenge_expired"
    CHALLENGE_REUSED = "challenge_reused"
    K1_EXPIRED = "k1_expired"
    K1_REUSED = "k1_reused"
    UNEXPECTED_K1 = "unexpected_k1"
    WRONG_DOMAIN = "wrong_domain"
    WRONG_NETWORK = "wrong_network"
    WRONG_ACTION = "wrong_action"
    PRINCIPAL_REVOKED = "principal_revoked"
    PRINCIPAL_SUSPENDED = "principal_suspended"
    DEVICE_REVOKED = "device_revoked"
    DEVICE_UNTRUSTED = "device_untrusted"
    SESSION_EXPIRED = "session_expired"
    SESSION_REVOKED = "session_revoked"
    SESSION_FROZEN = "session_frozen"
    NONCE_REUSED = "nonce_reused"
    STALE_TIMESTAMP = "stale_timestamp"
    BODY_HASH_MISMATCH = "body_hash_mismatch"
    SCOPE_MISSING = "scope_missing"
    METRIC_NOT_ALLOWED = "metric_not_allowed"
    QUOTA_EXCEEDED = "quota_exceeded"
    ENTITLEMENT_EXPIRED = "entitlement_expired"
    ENTITLEMENT_MISSING = "entitlement_missing"
    STEP_UP_REQUIRED = "step_up_required"
    POLICY_DENIED = "policy_denied"
    PAYMENT_UNSETTLED = "payment_unsettled"
    PAYMENT_EXPIRED = "payment_expired"
    PAYMENT_VERIFICATION_FAILED = "payment_verification_failed"
    WITHDRAW_POLICY_DENIED = "withdraw_policy_denied"
    WITHDRAW_LIMIT_EXCEEDED = "withdraw_limit_exceeded"
    RECOVERY_QUORUM_MISSING = "recovery_quorum_missing"
    COMPATIBILITY_PROOF_TOO_WEAK = "compatibility_proof_too_weak"
    INTERNAL_ERROR = "internal_error"
    UNKNOWN = "unknown"


class EndpointGroupLabel(StrEnum):
    WALLET_AUTH = "wallet_auth"
    LNURL_AUTH = "lnurl_auth"
    LNURL_PAY = "lnurl_pay"
    LNURL_WITHDRAW = "lnurl_withdraw"
    METRICS = "metrics"
    TRACE = "trace"
    TREASURY = "treasury"
    PAYREGISTER = "payregister"
    BUSINESS = "business"
    ENTERPRISE = "enterprise"
    RECOVERY = "recovery"
    ACCESS = "access"
    UNKNOWN = "unknown"


class ActionGroupLabel(StrEnum):
    API_KEY_MANAGEMENT = "api_key_management"
    SCOPE_MANAGEMENT = "scope_management"
    RECOVERY = "recovery"
    DEVICE_MANAGEMENT = "device_management"
    LOCKDOWN = "lockdown"
    TREASURY_POLICY = "treasury_policy"
    BUSINESS_ROLES = "business_roles"
    ENTERPRISE_POLICY = "enterprise_policy"
    PAYREGISTER_ADMIN = "payregister_admin"
    OFFLINE_ACCESS = "offline_access"
    DATA_EXPORT = "data_export"
    DELEGATED_ACCESS = "delegated_access"
    UNKNOWN = "unknown"


def normalize_label(value: object, enum: type[StrEnum], *, fallback: str = "unknown") -> str:
    """Map arbitrary input into an enum value; free text never reaches labels."""
    candidate = str(value.value if isinstance(value, StrEnum) else value or "").strip().lower()
    allowed = {item.value for item in enum}
    return candidate if candidate in allowed else fallback
