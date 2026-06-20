from pathlib import Path

import pytest

from app.storage.object_store.checksums import sha256_bytes
from app.storage.object_store.errors import ObjectStoreSecurityError, ObjectStoreSizeError
from app.storage.object_store.local_store import LocalObjectStore
from app.storage.object_store.schemas import ObjectWriteRequest


def request_for_key(object_key: str, metadata: dict[str, str] | None = None) -> ObjectWriteRequest:
    content = b"safe text"
    return ObjectWriteRequest(
        bucket="bastion-artifacts",
        object_key=object_key,
        content=content,
        content_type="text/plain",
        metadata=metadata or {"artifact_type": "proof_packet"},
        sha256=sha256_bytes(content),
    )


@pytest.mark.parametrize(
    "object_key", ["", "../escape.txt", "/absolute.txt", "proof/../../escape.txt"]
)
def test_rejects_empty_or_traversal_object_keys(tmp_path: Path, object_key: str) -> None:
    store = LocalObjectStore(root=tmp_path)
    with pytest.raises(ObjectStoreSecurityError):
        store.put_object(request_for_key(object_key))


def test_rejects_forbidden_object_key_material(tmp_path: Path) -> None:
    store = LocalObjectStore(root=tmp_path)
    with pytest.raises(ObjectStoreSecurityError, match="forbidden sensitive material"):
        store.put_object(request_for_key("proof/xprv-export.txt"))


def test_rejects_forbidden_metadata_material(tmp_path: Path) -> None:
    store = LocalObjectStore(root=tmp_path)
    with pytest.raises(ObjectStoreSecurityError, match="forbidden sensitive material"):
        store.put_object(request_for_key("proof/packet.txt", {"note": "private key export"}))


def test_rejects_binary_without_explicit_artifact_type(tmp_path: Path) -> None:
    store = LocalObjectStore(root=tmp_path)
    content = b"\x00\x01"
    request = ObjectWriteRequest(
        bucket="bastion-artifacts",
        object_key="proof/blob.bin",
        content=content,
        content_type="application/octet-stream",
        metadata={},
        sha256=sha256_bytes(content),
    )
    with pytest.raises(ObjectStoreSecurityError, match="artifact_type"):
        store.put_object(request)


def test_rejects_oversized_object(tmp_path: Path) -> None:
    store = LocalObjectStore(root=tmp_path, max_object_bytes=4)
    with pytest.raises(ObjectStoreSizeError):
        store.put_object(request_for_key("proof/packet.txt"))
