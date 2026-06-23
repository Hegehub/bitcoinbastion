"""
Access Layer package implementing Bastion Proof‑of‑Access Auth PQ.

This package provides skeleton models and services for a Bitcoin-native
authentication mechanism that replaces email/password logins with
cryptographic entitlements. It is intentionally minimal; concrete
implementations for payment proof collection, cryptographic signing,
session handling and policy enforcement must be provided by integrators.

See docs/ACCESS_LAYER.md for architecture and integration details.
"""

from .models import (
    PaymentProof,
    ApiEntitlements,
    SubscriptionEntitlement,
    AccessCertificate,
)
from .services import PaymentService, CertificateService, SessionService
from .policy import PolicyEngine, PolicyDecision
