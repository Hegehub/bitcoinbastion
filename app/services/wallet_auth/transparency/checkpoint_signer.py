"""Transparency signing adapter over the shared Bastion issuer envelope."""

from dataclasses import replace

from app.services.access.crypto.issuer_envelope import (
    BastionIssuedObjectType,
    build_classical_issuer_envelope,
)
from app.services.access.crypto.crypto_agility import CryptoProviderUnavailable
from app.services.access.crypto.migration_policy import SignatureRequirementPolicy

from .canonicalization import checkpoint_signed_payload
from .errors import CheckpointSignatureError, UnsupportedTransparencySignatureSuiteError
from .models import TransparencyCheckpoint


class TransparencyCheckpointSigner:
    def __init__(self, *, issuer_key_id: str, issuer_private_key: str) -> None:
        self.issuer_key_id = issuer_key_id
        self._issuer_private_key = issuer_private_key

    def sign(
        self,
        checkpoint: TransparencyCheckpoint,
        *,
        requirement: SignatureRequirementPolicy = SignatureRequirementPolicy.CLASSICAL_REQUIRED_PQ_OPTIONAL,
    ) -> TransparencyCheckpoint:
        if checkpoint.signature_suite != "ed25519":
            raise UnsupportedTransparencySignatureSuiteError("unsupported checkpoint signature suite")
        try:
            envelope = build_classical_issuer_envelope(
                checkpoint_signed_payload(checkpoint),
                object_type=BastionIssuedObjectType.TRANSPARENCY_CHECKPOINT,
                object_id_hash=checkpoint.checkpoint_id,
                object_fingerprint=checkpoint.checkpoint_hash,
                issuer_key_id=self.issuer_key_id,
                issuer_private_key=self._issuer_private_key,
                crypto_epoch=checkpoint.crypto_epoch,
                policy_epoch=checkpoint.policy_epoch,
                schema_epoch=checkpoint.schema_epoch,
                expires_at=checkpoint.expires_at,
                requirement=requirement,
            )
        except (CryptoProviderUnavailable, TypeError, ValueError) as exc:
            raise CheckpointSignatureError("checkpoint signing failed") from exc
        return replace(checkpoint, issuer_envelope=envelope.to_dict())
