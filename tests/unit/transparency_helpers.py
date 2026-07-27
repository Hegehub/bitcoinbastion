import base64
from datetime import UTC, datetime

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from app.services.wallet_auth.transparency import (
    CheckpointStream,
    InMemoryTransparencyRepository,
    TransparencyCheckpointBuilder,
    TransparencyCheckpointSigner,
    TransparencyCheckpointType,
    TransparencyLeafCommitment,
)

PRIVATE = "AQIDBAUGBwgJCgsMDQ4PEBESExQVFhcYGRobHB0eHyA"


def public_key() -> str:
    raw = base64.urlsafe_b64decode(PRIVATE + "=")
    public = Ed25519PrivateKey.from_private_bytes(raw).public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw
    )
    return base64.urlsafe_b64encode(public).rstrip(b"=").decode()


def leaf(kind: str = "policy", suffix: str = "1") -> TransparencyLeafCommitment:
    return TransparencyLeafCommitment(
        kind, f"sha256:{suffix.zfill(64)}", 1, 1, datetime(2026, 7, 27, tzinfo=UTC),
        "sha256:policy", "sha256:status", "sha256:metadata"
    )


def builder() -> tuple[TransparencyCheckpointBuilder, InMemoryTransparencyRepository]:
    repository = InMemoryTransparencyRepository()
    signer = TransparencyCheckpointSigner(issuer_key_id="issuer-v1", issuer_private_key=PRIVATE)
    return TransparencyCheckpointBuilder(repository=repository, signer=signer), repository


def stream(kind: TransparencyCheckpointType = TransparencyCheckpointType.POLICY_EPOCH) -> CheckpointStream:
    return CheckpointStream(kind, "test", "bastion-access")
