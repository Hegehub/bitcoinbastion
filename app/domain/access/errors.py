"""Pure domain exceptions for Bastion Proof-of-Access Auth."""

from __future__ import annotations


class AccessDomainError(ValueError):
    """Base exception for Access domain validation errors.

    Error messages must remain generic and must never include raw passes,
    private keys, recovery phrases, signatures, sessions, or other secrets.
    """


class InvalidPlanCodeError(AccessDomainError):
    """Raised when a plan code is not one of the stable Access plan values."""


class InvalidScopeError(AccessDomainError):
    """Raised when an Access scope is unknown or malformed."""


class ForbiddenScopeError(AccessDomainError):
    """Raised when a forbidden broad scope appears in an entitlement."""


class MetricGroupNotAllowedError(AccessDomainError):
    """Raised when a metric group is not allowed for a plan."""


class PlanEntitlementError(AccessDomainError):
    """Raised when a plan entitlement mapping violates domain rules."""


class AccessChallengeError(AccessDomainError):
    """Base class for Access challenge service errors."""


class AccessCertificateNotFoundError(AccessChallengeError):
    """Raised when a challenge references an unknown certificate."""


class AccessCertificateInactiveError(AccessChallengeError):
    """Raised when a certificate cannot create a challenge."""


class AccessCertificateExpiredError(AccessChallengeError):
    """Raised when a certificate is expired."""


class SubscriptionEntitlementInactiveError(AccessChallengeError):
    """Raised when no active entitlement exists for challenge scopes."""


class RequestedScopeNotAllowedError(AccessChallengeError):
    """Raised when requested scopes exceed entitlement scopes."""


class UnknownScopeError(AccessChallengeError):
    """Raised when a requested scope is not part of the Access scope catalog."""


class UnsafeScopeError(AccessChallengeError):
    """Raised when a forbidden broad scope is requested."""


class OriginRequiredError(AccessChallengeError):
    """Raised when an origin is missing."""


class InvalidOriginError(AccessChallengeError):
    """Raised when an origin cannot be normalized safely."""


class ChallengeNotFoundError(AccessChallengeError):
    """Raised when a challenge cannot be found."""


class ChallengeExpiredError(AccessChallengeError):
    """Raised when a challenge is expired."""


class ChallengeAlreadyUsedError(AccessChallengeError):
    """Raised when a challenge has already been used."""


class ChallengeRevokedError(AccessChallengeError):
    """Raised when a challenge has been revoked."""


class ChallengeOriginMismatchError(AccessChallengeError):
    """Raised when a challenge is used from a different origin."""


class AccessSessionError(AccessDomainError):
    """Base class for Proof-of-Possession session service errors."""


class DeviceNotFoundError(AccessSessionError):
    """Raised when a session request references an unknown device."""


class DeviceInactiveError(AccessSessionError):
    """Raised when a device cannot create or validate a session."""


class EntitlementMissingError(AccessSessionError):
    """Raised when no entitlement is available for session validation."""


class EntitlementExpiredError(AccessSessionError):
    """Raised when an entitlement has expired."""


class EntitlementInactiveError(AccessSessionError):
    """Raised when an entitlement status cannot authorize a session."""


class TargetRevokedError(AccessSessionError):
    """Raised when revocation registry denies an access target."""


class InvalidChallengeSignatureError(AccessSessionError):
    """Raised when a device challenge signature cannot be verified."""


class SessionNotFoundError(AccessSessionError):
    """Raised when a session token does not map to an active session row."""


class SessionExpiredError(AccessSessionError):
    """Raised when a session is expired."""


class SessionRevokedError(AccessSessionError):
    """Raised when a session was revoked."""


class SessionFrozenError(AccessSessionError):
    """Raised when a session was frozen."""


class MissingRequiredScopeError(AccessSessionError):
    """Raised when a session does not contain all required scopes."""


class AccessAuditError(AccessDomainError):
    """Raised when Access Audit Chain recording or verification fails."""
