from __future__ import annotations

import hashlib
import hmac
from typing import Protocol, runtime_checkable
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey


@runtime_checkable
class DeviceSigner(Protocol):
    @property
    def public_key(self) -> bytes: ...

    @property
    def fingerprint(self) -> str: ...

    def sign(self, digest: bytes) -> bytes: ...


class InMemoryDeviceSigner:
    """Test/development signer; production callers should supply vault-backed signers.

    This key authenticates Bastion requests only. It is never a Bitcoin wallet key.
    """

    def __init__(self, key: bytes) -> None:
        if len(key) < 32:
            raise ValueError("Device signing key must contain at least 32 random bytes")
        self._key = bytearray(key)

    @property
    def public_key(self) -> bytes:
        return hashlib.sha256(bytes(self._key)).digest()

    @property
    def fingerprint(self) -> str:
        return "sha256:" + hashlib.sha256(self.public_key).hexdigest()

    def sign(self, digest: bytes) -> bytes:
        return hmac.new(bytes(self._key), digest, hashlib.sha256).digest()

    def wipe(self) -> None:
        for index in range(len(self._key)):
            self._key[index] = 0

    def __repr__(self) -> str:
        return f"InMemoryDeviceSigner(fingerprint={self.fingerprint!r}, key='<redacted>')"


class Ed25519DeviceSigner:
    """Export-controlled Ed25519 Bastion Device signer (never a Bitcoin key)."""

    def __init__(self, private_key: Ed25519PrivateKey) -> None:
        self._private_key = private_key

    @classmethod
    def generate(cls) -> "Ed25519DeviceSigner":
        return cls(Ed25519PrivateKey.generate())

    @classmethod
    def from_private_bytes(cls, value: bytes) -> "Ed25519DeviceSigner":
        return cls(Ed25519PrivateKey.from_private_bytes(value))

    @property
    def public_key(self) -> bytes:
        return self._private_key.public_key().public_bytes(
            serialization.Encoding.Raw, serialization.PublicFormat.Raw
        )

    @property
    def fingerprint(self) -> str:
        payload = b"bastion-device-public-key-v1\x00ed25519\x00" + self.public_key
        return "sha256:" + hashlib.sha256(payload).hexdigest()

    def sign(self, digest: bytes) -> bytes:
        return self._private_key.sign(digest)

    def private_bytes_for_vault(self) -> bytes:
        """Return raw key material only for an application-controlled encrypted vault."""
        return self._private_key.private_bytes(
            serialization.Encoding.Raw,
            serialization.PrivateFormat.Raw,
            serialization.NoEncryption(),
        )

    def __repr__(self) -> str:
        return f"Ed25519DeviceSigner(fingerprint={self.fingerprint!r}, key='<redacted>')"
