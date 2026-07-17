"""Pure LNURL-auth domain primitives."""

from __future__ import annotations

from enum import StrEnum


class LNURLAuthAction(StrEnum):
    REGISTER = "register"
    LOGIN = "login"
    LINK = "link"
    AUTH = "auth"


class BastionLNURLIntentAction(StrEnum):
    PRINCIPAL_REGISTER = "principal_register"
    PRINCIPAL_LOGIN = "principal_login"
    PRINCIPAL_LINK = "principal_link"
    SESSION_CREATE = "session_create"
    DEVICE_ADD = "device_add"
    CREATE_API_KEY = "create_api_key"
    INCREASE_SCOPE = "increase_scope"
    RECOVERY_START = "recovery_start"
    RECOVERY_COMPLETE = "recovery_complete"
    LOCKDOWN_START = "lockdown_start"
    LOCKDOWN_RELEASE = "lockdown_release"
    BUSINESS_ROLE_CHANGE = "business_role_change"
    PAYREGISTER_OWNER_ACTION = "payregister_owner_action"
    PAYREGISTER_ADMIN_ENABLE = "payregister_admin_enable"
    ENTERPRISE_POLICY_CHANGE = "enterprise_policy_change"
    EXPORT_DATA = "export_data"
    CREATE_DELEGATED_PASS = "create_delegated_pass"
    TREASURY_POLICY_CHANGE = "treasury_policy_change"
    RECOVERY_CHANGE = "recovery_change"
    DEVICE_REVOKE = "device_revoke"
    BUSINESS_ROLE_ASSIGNMENT = "business_role_assignment"
    PAYREGISTER_DEVICE_ENROLL = "payregister_device_enroll"
    OFFLINE_PACK_ISSUE = "offline_pack_issue"
    REFUND_APPROVE = "refund_approve"
    PAYOUT_APPROVE = "payout_approve"


DEFAULT_LNURL_ACTION_INTENT_MAP = {
    LNURLAuthAction.REGISTER: BastionLNURLIntentAction.PRINCIPAL_REGISTER,
    LNURLAuthAction.LOGIN: BastionLNURLIntentAction.PRINCIPAL_LOGIN,
    LNURLAuthAction.LINK: BastionLNURLIntentAction.PRINCIPAL_LINK,
    LNURLAuthAction.AUTH: BastionLNURLIntentAction.SESSION_CREATE,
}
LNURL_AUTH_ALLOWED_ACTIONS = frozenset(LNURLAuthAction)


class LNURLAuthAttemptStatus(StrEnum):
    CREATED = "created"
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"
    EXPIRED = "expired"
    REPLAYED = "replayed"
    REVOKED = "revoked"
    FAILED = "failed"


class LNURLK1Status(StrEnum):
    UNUSED = "unused"
    USED = "used"
    EXPIRED = "expired"
    REVOKED = "revoked"
    REJECTED = "rejected"


LNURLAuthStatus = LNURLAuthAttemptStatus

_AUTH_ATTEMPT_TRANSITIONS = {
    LNURLAuthAttemptStatus.CREATED: frozenset({LNURLAuthAttemptStatus.PENDING, LNURLAuthAttemptStatus.EXPIRED, LNURLAuthAttemptStatus.REVOKED}),
    LNURLAuthAttemptStatus.PENDING: frozenset({LNURLAuthAttemptStatus.VERIFIED, LNURLAuthAttemptStatus.REJECTED, LNURLAuthAttemptStatus.EXPIRED, LNURLAuthAttemptStatus.REPLAYED, LNURLAuthAttemptStatus.REVOKED, LNURLAuthAttemptStatus.FAILED}),
    LNURLAuthAttemptStatus.REPLAYED: frozenset(),
    LNURLAuthAttemptStatus.VERIFIED: frozenset(),
    LNURLAuthAttemptStatus.REJECTED: frozenset(),
    LNURLAuthAttemptStatus.EXPIRED: frozenset(),
    LNURLAuthAttemptStatus.REVOKED: frozenset(),
    LNURLAuthAttemptStatus.FAILED: frozenset(),
}
_K1_TRANSITIONS = {
    LNURLK1Status.UNUSED: frozenset({LNURLK1Status.USED, LNURLK1Status.EXPIRED, LNURLK1Status.REVOKED, LNURLK1Status.REJECTED}),
    LNURLK1Status.USED: frozenset(),
    LNURLK1Status.EXPIRED: frozenset(),
    LNURLK1Status.REVOKED: frozenset(),
    LNURLK1Status.REJECTED: frozenset(),
}


def can_transition_auth_attempt(current: LNURLAuthAttemptStatus | str, target: LNURLAuthAttemptStatus | str) -> bool:
    return LNURLAuthAttemptStatus(target) in _AUTH_ATTEMPT_TRANSITIONS[LNURLAuthAttemptStatus(current)]


def can_transition_k1(current: LNURLK1Status | str, target: LNURLK1Status | str) -> bool:
    return LNURLK1Status(target) in _K1_TRANSITIONS[LNURLK1Status(current)]
