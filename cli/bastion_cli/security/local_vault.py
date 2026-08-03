from __future__ import annotations

import base64
import json
import os
import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

_AAD = b"bitcoin-bastion-cli-v1"
_FORBIDDEN = {
    "seed",
    "seedphrase",
    "mnemonic",
    "privatekey",
    "walletprivatekey",
    "xprv",
    "bitcoinseed",
    "lightningseed",
}
SAFETY_MESSAGE = "Bitcoin Bastion does not require your Bitcoin wallet seed or private key."


def default_vault_path() -> Path:
    root = os.getenv("XDG_STATE_HOME")
    return (
        Path(root).expanduser() / "bitcoin-bastion" / "vault.bin"
        if root
        else Path.home() / ".local" / "state" / "bitcoin-bastion" / "vault.bin"
    )


def reject_wallet_secrets(value: Any) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if str(key).replace("_", "").replace("-", "").casefold() in _FORBIDDEN:
                raise ValueError(SAFETY_MESSAGE)
            reject_wallet_secrets(item)
    elif isinstance(value, list):
        for item in value:
            reject_wallet_secrets(item)


@dataclass(slots=True)
class LocalVault:
    """Explicit passphrase-encrypted CLI state with restrictive Unix permissions."""

    path: Path
    passphrase: str

    @classmethod
    def from_environment(cls) -> "LocalVault | None":
        phrase = os.getenv("BB_CLI_VAULT_PASSPHRASE")
        return cls(default_vault_path(), phrase) if phrase else None

    def load(self) -> dict[str, Any]:
        if not self.path.exists():
            return {}
        envelope = json.loads(self.path.read_text(encoding="utf-8"))
        salt = base64.b64decode(envelope["salt"])
        nonce = base64.b64decode(envelope["nonce"])
        ciphertext = base64.b64decode(envelope["ciphertext"])
        plaintext = AESGCM(self._key(salt)).decrypt(nonce, ciphertext, _AAD)
        result = cast(dict[str, Any], json.loads(plaintext))
        reject_wallet_secrets(result)
        return result

    def save(self, state: dict[str, Any]) -> None:
        reject_wallet_secrets(state)
        salt, nonce = os.urandom(16), os.urandom(12)
        ciphertext = AESGCM(self._key(salt)).encrypt(
            nonce, json.dumps(state, separators=(",", ":")).encode(), _AAD
        )
        self.path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(
                {
                    "salt": base64.b64encode(salt).decode(),
                    "nonce": base64.b64encode(nonce).decode(),
                    "ciphertext": base64.b64encode(ciphertext).decode(),
                }
            ),
            encoding="utf-8",
        )
        os.chmod(temporary, 0o600)
        temporary.replace(self.path)
        os.chmod(self.path, 0o600)

    def clear(self) -> None:
        self.path.unlink(missing_ok=True)

    def _key(self, salt: bytes) -> bytes:
        return hashlib.scrypt(self.passphrase.encode(), salt=salt, n=2**14, r=8, p=1, dklen=32)
