"""Safe exception types for Access signature primitives."""

from __future__ import annotations


class SignatureError(Exception):
    """Base class for signature-suite errors with sanitized messages."""


class UnsupportedSignatureSuite(SignatureError):
    """Raised when a known or unknown signature suite is not implemented."""


class InvalidSignature(SignatureError):
    """Raised for malformed signature material when exception style is required."""


class MissingIssuerKey(SignatureError):
    """Raised when issuer signing configuration is missing."""


class InvalidIssuerKey(SignatureError):
    """Raised when issuer private-key material cannot be loaded safely."""


class InvalidPublicKey(SignatureError):
    """Raised when public-key material cannot be loaded safely."""


class UnsafeKeyMaterialError(SignatureError):
    """Raised when key material looks like a placeholder or forbidden secret type."""
