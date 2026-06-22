from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

ArtifactType = Literal[
    "proof_packet",
    "trace_report_export",
    "evidence_archive",
    "release_evidence",
    "migration_evidence",
    "backup_restore_evidence",
    "sbom",
    "provenance",
    "signed_receipt",
    "audit_export",
    "enterprise_evidence_bundle",
    "generic",
]
ArtifactDomain = Literal[
    "trace",
    "evidence",
    "deployment",
    "release",
    "backup",
    "access",
    "payregister",
    "market",
    "news",
    "treasury",
    "observability",
    "generic",
]
ArtifactStatus = Literal["pending", "available", "failed", "deleted", "quarantined"]
EncryptionStatus = Literal["unknown", "none", "server_side", "client_side"]
RetentionPolicy = Literal[
    "ephemeral", "standard", "evidence", "compliance", "worm", "enterprise_custom"
]
RedactionStatus = Literal["not_required", "pending", "redacted", "failed"]

_FORBIDDEN_METADATA_TERMS = (
    "seed phrase",
    "private key",
    "xprv",
    "yprv",
    "zprv",
    "wallet.dat",
    "mnemonic",
    "raw password",
    "raw api secret",
)


def validate_no_sensitive_material(value: Any, field_name: str) -> Any:
    text = str(value).casefold()
    if any(term in text for term in _FORBIDDEN_METADATA_TERMS):
        raise ValueError(f"{field_name} contains forbidden sensitive material")
    return value


class StorageArtifactBase(BaseModel):
    artifact_type: ArtifactType = "generic"
    artifact_subtype: str | None = Field(default=None, max_length=80)
    domain: ArtifactDomain = "generic"
    object_uri: str = Field(min_length=1, max_length=2048)
    bucket: str = Field(min_length=1, max_length=255)
    object_key: str = Field(min_length=1, max_length=2048)
    sha256_hash: str = Field(min_length=64, max_length=64)
    size_bytes: int = Field(ge=0)
    content_type: str = Field(min_length=1, max_length=255)
    compression: str | None = Field(default=None, max_length=32)
    encryption_status: EncryptionStatus = "unknown"
    signature_alg: str | None = Field(default=None, max_length=64)
    signature_value: str | None = None
    signature_key_id: str | None = Field(default=None, max_length=160)
    retention_policy: RetentionPolicy = "standard"
    retention_until: datetime | None = None
    legal_hold: bool = False
    redaction_status: RedactionStatus = "not_required"
    access_policy_json: dict[str, Any] = Field(default_factory=dict)
    metadata_json: dict[str, Any] = Field(default_factory=dict)
    created_by_hash: str | None = Field(default=None, max_length=160)
    status: ArtifactStatus = "available"

    @field_validator("sha256_hash")
    @classmethod
    def validate_sha256_hash(cls, value: str) -> str:
        normalized = value.strip()
        if len(normalized) != 64 or any(char not in "0123456789abcdef" for char in normalized):
            raise ValueError("sha256_hash must be 64 lowercase hexadecimal characters")
        return normalized

    @field_validator("object_key", "bucket", "object_uri", "created_by_hash", mode="after")
    @classmethod
    def reject_sensitive_strings(cls, value: str | None) -> str | None:
        if value is not None:
            validate_no_sensitive_material(value, "storage artifact field")
        return value

    @model_validator(mode="after")
    def reject_sensitive_json(self) -> "StorageArtifactBase":
        validate_no_sensitive_material(self.access_policy_json, "access_policy_json")
        validate_no_sensitive_material(self.metadata_json, "metadata_json")
        return self


class StorageArtifactCreate(StorageArtifactBase):
    artifact_id: str | None = Field(default=None, max_length=80)


class StorageArtifactUpdate(BaseModel):
    artifact_subtype: str | None = Field(default=None, max_length=80)
    signature_alg: str | None = Field(default=None, max_length=64)
    signature_value: str | None = None
    signature_key_id: str | None = Field(default=None, max_length=160)
    retention_policy: RetentionPolicy | None = None
    retention_until: datetime | None = None
    legal_hold: bool | None = None
    redaction_status: RedactionStatus | None = None
    access_policy_json: dict[str, Any] | None = None
    metadata_json: dict[str, Any] | None = None
    status: ArtifactStatus | None = None

    @model_validator(mode="after")
    def reject_sensitive_json(self) -> "StorageArtifactUpdate":
        if self.access_policy_json is not None:
            validate_no_sensitive_material(self.access_policy_json, "access_policy_json")
        if self.metadata_json is not None:
            validate_no_sensitive_material(self.metadata_json, "metadata_json")
        return self


class StorageArtifactRead(StorageArtifactBase):
    id: int
    artifact_id: str
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None

    model_config = {"from_attributes": True}


class StorageArtifactListResponse(BaseModel):
    items: list[StorageArtifactRead]
    total: int
    limit: int
    offset: int
