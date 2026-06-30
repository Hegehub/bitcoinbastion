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
