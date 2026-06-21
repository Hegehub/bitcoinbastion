from hashlib import sha256
from pathlib import Path

import pytest

from app.storage.object_store.checksums import sha256_bytes, sha256_file, validate_sha256
from app.storage.object_store.errors import ObjectStoreChecksumError


def test_sha256_bytes_and_file_match(tmp_path: Path) -> None:
    data = b"bitcoin-bastion-artifact"
    path = tmp_path / "artifact.bin"
    path.write_bytes(data)
    assert sha256_bytes(data) == sha256_file(path)


def test_sha256_is_deterministic_for_same_bytes() -> None:
    data = b"deterministic-storage-evidence"
    assert sha256_bytes(data) == sha256_bytes(data)


def test_different_bytes_produce_different_checksums() -> None:
    assert sha256_bytes(b"artifact-a") != sha256_bytes(b"artifact-b")


def test_empty_bytes_checksum_is_explicit() -> None:
    assert sha256_bytes(b"") == sha256(b"").hexdigest()


def test_checksum_has_plain_hex_shape_without_prefix() -> None:
    checksum = sha256_bytes(b"shape")
    assert len(checksum) == 64
    assert checksum == checksum.lower()
    assert not checksum.startswith("sha256:")


def test_checksum_mismatch_raises_typed_error() -> None:
    with pytest.raises(ObjectStoreChecksumError, match="mismatch"):
        validate_sha256("abc", "def")


def test_missing_checksum_raises_typed_error() -> None:
    with pytest.raises(ObjectStoreChecksumError, match="required"):
        validate_sha256("abc", None)
