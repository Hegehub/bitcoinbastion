from __future__ import annotations

import base64
import hashlib
import hmac
from dataclasses import dataclass
from typing import Protocol


class DeviceSigner(Protocol):
    def public_key(self) -> str: ...

    def public_key_fingerprint(self) -> str: ...

    def sign(self, payload: bytes) -> str: ...


@dataclass(frozen=True)
class InMemoryDeviceSigner:
    """Test/developer signer for Bastion Access only; never use Bitcoin wallet keys."""

    secret: bytes
    public_key_value: str = "bastion-test-device-key"

    def public_key(self) -> str:
        return self.public_key_value

    def public_key_fingerprint(self) -> str:
        digest = hashlib.sha256(self.public_key_value.encode()).hexdigest()
        return f"sha256:{digest}"

    def sign(self, payload: bytes) -> str:
        digest = hmac.new(self.secret, payload, hashlib.sha256).digest()
        return "hmac-sha256:" + base64.b64encode(digest).decode("ascii")
