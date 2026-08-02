"""Issuer public-key lifecycle registry; private bytes are never persisted here."""

from dataclasses import dataclass, replace
from datetime import datetime
from enum import StrEnum

from app.services.access.crypto.algorithms import SignatureAlgorithm


class IssuerKeyStatus(StrEnum):
    PENDING = "pending"
    ACTIVE = "active"
    VERIFY_ONLY = "verify_only"
    RETIRING = "retiring"
    RETIRED = "retired"
    REVOKED = "revoked"
    COMPROMISED = "compromised"
    DISABLED = "disabled"


class IssuerKeyProviderType(StrEnum):
    ENVIRONMENT = "environment"
    FILE_REFERENCE = "file_reference"
    HSM = "hsm"
    KMS = "kms"
    VAULT_PROVIDER = "vault_provider"
    EXTERNAL_SIGNER = "external_signer"
    DISABLED = "disabled"


@dataclass(frozen=True, slots=True)
class IssuerKeyRecord:
    key_id: str
    algorithm: SignatureAlgorithm
    key_fingerprint: str
    public_key_reference: str
    private_key_provider_reference: str | None
    status: IssuerKeyStatus
    created_at: datetime
    activated_at: datetime | None
    retire_at: datetime | None
    revoked_at: datetime | None
    crypto_epoch: int
    allowed_object_types: frozenset[str]
    can_sign: bool
    can_verify: bool
    hardware_backed: bool
    provider_type: IssuerKeyProviderType

    def __post_init__(self) -> None:
        forbidden = ("-----BEGIN", "PRIVATE KEY", "base64:")
        if self.private_key_provider_reference and any(
            item in self.private_key_provider_reference for item in forbidden
        ):
            raise ValueError("Private key provider reference must not contain key material")


class IssuerKeyRegistry:
    def __init__(self) -> None:
        self._records: dict[str, IssuerKeyRecord] = {}

    def register(self, record: IssuerKeyRecord) -> None:
        if record.key_id in self._records:
            raise ValueError("Issuer key already registered")
        self._records[record.key_id] = record

    def resolve_for_signing(self, key_id: str, object_type: str) -> IssuerKeyRecord:
        record = self.get(key_id)
        if (
            record.status not in {IssuerKeyStatus.ACTIVE, IssuerKeyStatus.RETIRING}
            or not record.can_sign
        ):
            raise IssuerKeyUnavailable("Issuer key cannot sign")
        if object_type not in record.allowed_object_types:
            raise IssuerKeyUnavailable("Issuer key is not allowed for object type")
        return record

    def resolve_for_verification(self, key_id: str) -> IssuerKeyRecord:
        record = self.get(key_id)
        if record.status in {
            IssuerKeyStatus.REVOKED,
            IssuerKeyStatus.COMPROMISED,
            IssuerKeyStatus.DISABLED,
        }:
            raise IssuerKeyUnavailable(f"Issuer key status is {record.status.value}")
        if not record.can_verify:
            raise IssuerKeyUnavailable("Issuer key cannot verify")
        return record

    def transition(self, key_id: str, status: IssuerKeyStatus, at: datetime) -> IssuerKeyRecord:
        current = self.get(key_id)
        updated = replace(
            current,
            status=status,
            revoked_at=at
            if status in {IssuerKeyStatus.REVOKED, IssuerKeyStatus.COMPROMISED}
            else current.revoked_at,
            can_sign=current.can_sign
            and status in {IssuerKeyStatus.ACTIVE, IssuerKeyStatus.RETIRING},
        )
        self._records[key_id] = updated
        return updated

    def get(self, key_id: str) -> IssuerKeyRecord:
        try:
            return self._records[key_id]
        except KeyError as exc:
            raise IssuerKeyUnavailable("Unknown issuer key") from exc


class IssuerKeyUnavailable(RuntimeError):
    pass
