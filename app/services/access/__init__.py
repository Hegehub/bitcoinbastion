"""Access Layer service foundations with lazy public exports."""

from __future__ import annotations

from typing import Any

__all__ = [
    "AccessAuditChain",
    "AccessAuditEventType",
    "AccessChallengeResult",
    "AccessChallengeService",
    "AccessPolicyContext",
    "AccessPolicyDecision",
    "AccessPolicyEngine",
    "AccessRequestHeaders",
    "AccessRequestVerifier",
    "AccessSessionContext",
    "AccessSessionCreateResult",
    "AccessSessionService",
    "RevocationRegistry",
    "RevocationStatus",
    "VerifiedAccessRequest",
]

_EXPORT_MODULES = {
    "AccessAuditChain": "app.services.access.audit_chain",
    "AccessAuditEventType": "app.services.access.audit_chain",
    "AccessChallengeResult": "app.services.access.challenge_service",
    "AccessChallengeService": "app.services.access.challenge_service",
    "AccessPolicyContext": "app.services.access.policy_context",
    "AccessPolicyDecision": "app.services.access.policy_context",
    "AccessPolicyEngine": "app.services.access.policy_engine",
    "AccessRequestHeaders": "app.services.access.request_verifier",
    "AccessRequestVerifier": "app.services.access.request_verifier",
    "AccessSessionContext": "app.services.access.session_service",
    "AccessSessionCreateResult": "app.services.access.session_service",
    "AccessSessionService": "app.services.access.session_service",
    "RevocationRegistry": "app.services.access.revocation_registry",
    "RevocationStatus": "app.services.access.revocation_registry",
    "VerifiedAccessRequest": "app.services.access.request_verifier",
}


def __getattr__(name: str) -> Any:
    if name not in _EXPORT_MODULES:
        raise AttributeError(name)
    from importlib import import_module

    module = import_module(_EXPORT_MODULES[name])
    value = getattr(module, name)
    globals()[name] = value
    return value
