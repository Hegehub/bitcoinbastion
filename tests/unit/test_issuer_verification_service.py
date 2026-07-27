from datetime import UTC, datetime

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from app.services.access.crypto.algorithms import SignatureAlgorithm
from app.services.access.crypto.crypto_agility import CryptoCapabilityRegistry
from app.services.access.crypto.issuer_envelope import (
    BastionIssuedObjectType,
    BastionIssuerVerificationService,
    build_classical_issuer_envelope,
)
from app.services.access.crypto.key_registry import (
    IssuerKeyProviderType,
    IssuerKeyRecord,
    IssuerKeyRegistry,
    IssuerKeyStatus,
)
from app.services.access.crypto.migration_policy import CryptoEpochRegistry


def test_existing_classical_object_verifies():
    raw = bytes(range(1, 33))
    key = Ed25519PrivateKey.from_private_bytes(raw)
    private = "AQIDBAUGBwgJCgsMDQ4PEBESExQVFhcYGRobHB0eHyA"
    public = (
        key.public_key()
        .public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)
        .decode()
    )
    payload = {"plan": "plus_pass"}
    envelope = build_classical_issuer_envelope(
        payload,
        object_type=BastionIssuedObjectType.WALLET_SUBSCRIPTION_ENTITLEMENT,
        object_id_hash="sha256:id",
        object_fingerprint="sha256:object",
        issuer_key_id="issuer",
        issuer_private_key=private,
    )
    keys = IssuerKeyRegistry()
    keys.register(
        IssuerKeyRecord(
            "issuer",
            SignatureAlgorithm.ED25519,
            envelope.issuer_key_fingerprint,
            "public:issuer",
            "env:key",
            IssuerKeyStatus.ACTIVE,
            datetime.now(UTC),
            datetime.now(UTC),
            None,
            None,
            1,
            frozenset({BastionIssuedObjectType.WALLET_SUBSCRIPTION_ENTITLEMENT.value}),
            True,
            True,
            False,
            IssuerKeyProviderType.ENVIRONMENT,
        )
    )
    service = BastionIssuerVerificationService(
        capabilities=CryptoCapabilityRegistry(),
        keys=keys,
        epochs=CryptoEpochRegistry(),
        public_key_resolver=lambda _: public,
    )
    assert service.verify(payload, envelope).verified
    assert not service.verify({"plan": "tampered"}, envelope).verified
