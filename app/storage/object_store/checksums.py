"""SHA-256 helpers for Object Storage artifacts."""

from hashlib import sha256
from pathlib import Path

from app.storage.object_store.errors import ObjectStoreChecksumError


def sha256_bytes(data: bytes) -> str:
    return sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as file_obj:
        for chunk in iter(lambda: file_obj.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_sha256(actual: str, expected: str | None) -> None:
    if not expected:
        raise ObjectStoreChecksumError("SHA-256 checksum is required for stored objects.")
    if actual.lower() != expected.lower():
        raise ObjectStoreChecksumError("SHA-256 checksum mismatch for stored object.")
