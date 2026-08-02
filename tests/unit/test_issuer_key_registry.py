from datetime import UTC, datetime

import pytest

from app.services.access.crypto.algorithms import SignatureAlgorithm
from app.services.access.crypto.key_registry import (
    IssuerKeyProviderType,
    IssuerKeyRecord,
    IssuerKeyRegistry,
    IssuerKeyStatus,
    IssuerKeyUnavailable,
)


def record():
    return IssuerKeyRecord(
        "issuer-1",
        SignatureAlgorithm.ED25519,
        "sha256:key",
        "public:key-1",
        "env:ACCESS_ISSUER_PRIVATE_KEY",
        IssuerKeyStatus.ACTIVE,
        datetime.now(UTC),
        datetime.now(UTC),
        None,
        None,
        1,
        frozenset({"access_certificate"}),
        True,
        True,
        False,
        IssuerKeyProviderType.ENVIRONMENT,
    )


def test_key_lifecycle_blocks_revoked_signing_without_storing_private_bytes():
    registry = IssuerKeyRegistry()
    registry.register(record())
    assert "PRIVATE KEY" not in repr(registry.get("issuer-1"))
    registry.transition("issuer-1", IssuerKeyStatus.REVOKED, datetime.now(UTC))
    with pytest.raises(IssuerKeyUnavailable):
        registry.resolve_for_signing("issuer-1", "access_certificate")
