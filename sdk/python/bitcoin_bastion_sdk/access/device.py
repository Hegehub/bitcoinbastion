from __future__ import annotations

import hashlib
import hmac
from typing import Protocol, runtime_checkable


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
