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


def test_revoked_issuer_key_cannot_sign():
    registry = IssuerKeyRegistry()
    now = datetime.now(UTC)
    registry.register(
        IssuerKeyRecord(
            "issuer",
            SignatureAlgorithm.ED25519,
            "sha256:key",
            "public:issuer",
            "env:key",
            IssuerKeyStatus.ACTIVE,
            now,
            now,
            None,
            None,
            1,
            frozenset({"access_certificate"}),
            True,
            True,
            False,
            IssuerKeyProviderType.ENVIRONMENT,
        )
    )
    registry.transition("issuer", IssuerKeyStatus.REVOKED, now)
    with pytest.raises(IssuerKeyUnavailable):
        registry.resolve_for_signing("issuer", "access_certificate")
