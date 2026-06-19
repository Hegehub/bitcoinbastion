"""Lightweight schemas for Object Storage requests and results."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from pathlib import Path
from typing import Mapping


class ObjectRetentionClass(StrEnum):
    TEMPORARY = "temporary"
    STANDARD = "standard"
    EVIDENCE = "evidence"
    RELEASE_EVIDENCE = "release_evidence"
    AUDIT_ARCHIVE = "audit_archive"
    ENTERPRISE_ARCHIVE = "enterprise_archive"


@dataclass(frozen=True)
class ObjectStoreConfig:
    backend: str = "disabled"
    bucket: str = ""
    endpoint: str = ""
    access_key: str = ""
    secret_key: str = ""
    secure: bool = True
    region: str | None = None
    local_root: Path = Path(".storage/objects")
    max_object_bytes: int = 100 * 1024 * 1024


@dataclass(frozen=True)
class ObjectStoreMetadata:
    bucket: str
    object_key: str
    content_type: str
    sha256: str
    size_bytes: int
    retention_class: ObjectRetentionClass = ObjectRetentionClass.STANDARD
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class ObjectWriteRequest:
    bucket: str
    object_key: str
    content: bytes
    content_type: str = "application/octet-stream"
    metadata: Mapping[str, str] = field(default_factory=dict)
    sha256: str | None = None
    size_bytes: int | None = None
    retention_class: ObjectRetentionClass = ObjectRetentionClass.STANDARD


@dataclass(frozen=True)
class ObjectReadResult:
    bucket: str
    object_key: str
    content: bytes
    content_type: str
    metadata: ObjectStoreMetadata


@dataclass(frozen=True)
class ObjectStatResult:
    bucket: str
    object_key: str
    content_type: str
    sha256: str
    size_bytes: int
    retention_class: ObjectRetentionClass
    created_at: datetime
    metadata: Mapping[str, str] = field(default_factory=dict)
