"""Backward-compatible imports for LNURL successAction domain primitives."""

from app.domain.lnurl.success_actions import (
    BastionSuccessActionPurpose,
    LNURLActivationPurpose,
    LNURLActivationStatus,
    LNURLSuccessActionDescriptor,
    LNURLSuccessActionType,
)

__all__ = [
    "BastionSuccessActionPurpose",
    "LNURLActivationPurpose",
    "LNURLActivationStatus",
    "LNURLSuccessActionDescriptor",
    "LNURLSuccessActionType",
]
