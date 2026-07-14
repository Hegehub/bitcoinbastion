"""Wallet proof verifier interfaces and models."""

from app.services.wallet_auth.verifiers.base import (
    WalletCompatibilityContext,
    WalletProofRevocationChecker,
    WalletProofRevocationUnavailable,
    WalletProofVerificationError,
    WalletProofVerificationMetrics,
    WalletProofVerificationReason,
    WalletProofVerificationRequest,
    WalletProofVerificationResult,
    WalletProofVerifier,
    proof_fingerprint_for_request,
    redact_verification_exception,
    wallet_identifier_hash_for_request,
)
from app.services.wallet_auth.verifiers.bip322 import BIP322Verifier, BIP322VerifierConfig, VerificationOutcome
from app.services.wallet_auth.verifiers.bip322_backend import (
    BIP322ScriptBackend,
    ConservativeBIP322ScriptBackend,
    ScriptVerificationOutcome,
    ScriptVerificationResult,
)
from app.services.wallet_auth.verifiers.bip322_codec import BIP322Variant, bip322_message_hash
from app.services.wallet_auth.verifiers.legacy_message import (
    LEGACY_SIGNATURE_ALLOWED_ACTIONS,
    LEGACY_SIGNATURE_FORBIDDEN_ACTIONS,
    LegacyBitcoinMessageVerifier,
    LegacyBitcoinMessageVerifierConfig,
)

__all__ = [
    "WalletCompatibilityContext",
    "WalletProofRevocationChecker",
    "WalletProofRevocationUnavailable",
    "WalletProofVerificationError",
    "WalletProofVerificationMetrics",
    "WalletProofVerificationReason",
    "WalletProofVerificationRequest",
    "WalletProofVerificationResult",
    "WalletProofVerifier",
    "proof_fingerprint_for_request",
    "redact_verification_exception",
    "wallet_identifier_hash_for_request",
    "BIP322Verifier",
    "BIP322VerifierConfig",
    "VerificationOutcome",
    "BIP322ScriptBackend",
    "ConservativeBIP322ScriptBackend",
    "ScriptVerificationOutcome",
    "ScriptVerificationResult",
    "BIP322Variant",
    "bip322_message_hash",
    "LegacyBitcoinMessageVerifier",
    "LegacyBitcoinMessageVerifierConfig",
    "LEGACY_SIGNATURE_ALLOWED_ACTIONS",
    "LEGACY_SIGNATURE_FORBIDDEN_ACTIONS",
]
