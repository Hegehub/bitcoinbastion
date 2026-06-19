from pathlib import Path

import pytest

from app.storage.object_store.checksums import sha256_bytes
from app.storage.object_store.errors import ObjectStoreChecksumError, ObjectStoreNotFoundError
from app.storage.object_store.local_store import LocalObjectStore
from app.storage.object_store.schemas import ObjectRetentionClass, ObjectWriteRequest


def write_request(content: bytes = b"hello") -> ObjectWriteRequest:
    return ObjectWriteRequest(
        bucket="bastion-artifacts",
        object_key="proof/packet.txt",
        content=content,
        content_type="text/plain",
        metadata={"artifact_type": "proof_packet"},
        sha256=sha256_bytes(content),
        retention_class=ObjectRetentionClass.EVIDENCE,
    )


def test_local_object_store_put_get_stat_exists_delete(tmp_path: Path) -> None:
    store = LocalObjectStore(root=tmp_path)
    request = write_request()

    stat = store.put_object(request)
    assert stat.sha256 == sha256_bytes(request.content)
    assert stat.size_bytes == len(request.content)
    assert stat.retention_class == ObjectRetentionClass.EVIDENCE
    assert store.object_exists(request.bucket, request.object_key) is True

    read_result = store.get_object(request.bucket, request.object_key)
    assert read_result.content == request.content
    assert read_result.metadata.sha256 == stat.sha256

    restat = store.stat_object(request.bucket, request.object_key)
    assert restat.sha256 == stat.sha256

    presigned = store.generate_presigned_get_url(request.bucket, request.object_key, 60)
    assert presigned.startswith("local://bastion-artifacts/proof/packet.txt")

    store.delete_object(request.bucket, request.object_key)
    assert store.object_exists(request.bucket, request.object_key) is False
    with pytest.raises(ObjectStoreNotFoundError):
        store.stat_object(request.bucket, request.object_key)


def test_local_object_store_rejects_bad_write_checksum(tmp_path: Path) -> None:
    store = LocalObjectStore(root=tmp_path)
    request = ObjectWriteRequest(
        bucket="bastion-artifacts",
        object_key="proof/packet.txt",
        content=b"hello",
        content_type="text/plain",
        metadata={"artifact_type": "proof_packet"},
        sha256="0" * 64,
    )
    with pytest.raises(ObjectStoreChecksumError):
        store.put_object(request)


def test_local_object_store_detects_corrupted_file(tmp_path: Path) -> None:
    store = LocalObjectStore(root=tmp_path)
    request = write_request()
    store.put_object(request)
    object_path = tmp_path / request.bucket / request.object_key
    object_path.write_bytes(b"corrupted")
    with pytest.raises(ObjectStoreChecksumError):
        store.get_object(request.bucket, request.object_key)


def test_local_root_path_is_respected(tmp_path: Path) -> None:
    store = LocalObjectStore(root=tmp_path)
    request = write_request()
    store.put_object(request)
    assert (tmp_path / request.bucket / request.object_key).exists()
    assert not (tmp_path.parent / request.bucket).exists()
