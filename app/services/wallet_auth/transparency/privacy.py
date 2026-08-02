"""Allowlist-first privacy validation and context-local commitments."""

from collections.abc import Mapping, Sequence
from typing import Any

from app.services.access.crypto.hashing import hmac_sha256_prefixed

from .errors import CheckpointPrivacyViolationError

PUBLIC_ARTIFACT_FIELDS = frozenset(
    {
        "type", "version", "checkpoint_id", "checkpoint_type", "stream", "epochs",
        "root_hash", "previous_checkpoint_hash", "checkpoint_hash", "source_count",
        "created_at", "expires_at", "issuer", "visibility", "hash_suite",
        "signature_suite", "environment", "metadata_commitment",
    }
)
FORBIDDEN_SOURCE_FIELDS = frozenset(
    {
        "bitcoin_address", "wallet_address", "wallet_public_key", "linking_key", "lnurl_key",
        "raw_k1", "k1", "wallet_signature", "session_token", "access_pass", "recovery_phrase",
        "recovery_file", "private_key", "mnemonic", "xprv", "invoice", "preimage",
        "payer_email", "payer_name", "raw_payer_data", "telegram_id", "raw_device_id",
        "principal_hash", "payment_hash",
    }
)


def context_commitment(*, secret: str, stream_context: str, value: str) -> str:
    if not stream_context:
        raise ValueError("stream context is required")
    return hmac_sha256_prefixed(secret, f"transparency:v1:{stream_context}:{value}")


def validate_source_metadata(value: Any, *, public_safe: bool) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            lowered = str(key).lower()
            if public_safe and lowered in FORBIDDEN_SOURCE_FIELDS:
                raise CheckpointPrivacyViolationError("public checkpoint source is not privacy-safe")
            validate_source_metadata(child, public_safe=public_safe)
    elif isinstance(value, Sequence) and not isinstance(value, str | bytes):
        for child in value:
            validate_source_metadata(child, public_safe=public_safe)


def sanitize_public_artifact(artifact: Mapping[str, Any]) -> dict[str, Any]:
    unknown = set(artifact) - PUBLIC_ARTIFACT_FIELDS
    if unknown:
        raise CheckpointPrivacyViolationError("public artifact contains non-allowlisted fields")
    validate_source_metadata(artifact, public_safe=True)
    return dict(artifact)
