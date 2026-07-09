"""LNURL-auth domain primitives."""

from __future__ import annotations

from enum import StrEnum


class LNURLAuthAction(StrEnum):
    REGISTER = "register"
    LOGIN = "login"
    LINK = "link"
    AUTH = "auth"


LNURL_AUTH_ALLOWED_ACTIONS = frozenset(LNURLAuthAction)


class LNURLAuthStatus(StrEnum):
    CHALLENGE_CREATED = "challenge_created"
    CALLBACK_RECEIVED = "callback_received"
    VERIFIED = "verified"
    FAILED = "failed"
    EXPIRED = "expired"
    USED = "used"
    REVOKED = "revoked"
