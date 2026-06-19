from pathlib import Path

import pytest

from app.storage.object_store.checksums import sha256_bytes, sha256_file, validate_sha256
from app.storage.object_store.errors import ObjectStoreChecksumError


def test_sha256_bytes_and_file_match(tmp_path: Path) -> None:
    data = b"bitcoin-bastion-artifact"
    path = tmp_path / "artifact.bin"
    path.write_bytes(data)
    assert sha256_bytes(data) == sha256_file(path)


def test_checksum_mismatch_raises_typed_error() -> None:
    with pytest.raises(ObjectStoreChecksumError, match="mismatch"):
        validate_sha256("abc", "def")


def test_missing_checksum_raises_typed_error() -> None:
    with pytest.raises(ObjectStoreChecksumError, match="required"):
        validate_sha256("abc", None)
