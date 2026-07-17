"""Production LNURL-pay metadata builder.

LNURL-pay metadata is wallet-visible payment context and future payment evidence.
It is deterministic and hash-committed, but it never grants access, proves
settlement, issues entitlements, or authorizes recovery/roles/API access.
"""

from __future__ import annotations

import base64
import binascii
import json
import re
from dataclasses import dataclass
from typing import ClassVar
from urllib.parse import urlparse

from app.domain.access.errors import InvalidPlanCodeError
from app.domain.access.plans import PlanCode, normalize_plan_code
from app.services.access.crypto.hashing import sha256_prefixed

TEXT_PLAIN = "text/plain"
TEXT_LONG_DESC = "text/long-desc"
TEXT_IDENTIFIER = "text/identifier"
IMAGE_PNG_BASE64 = "image/png;base64"
IMAGE_JPEG_BASE64 = "image/jpeg;base64"
ALLOWED_LNURL_PAY_METADATA_TYPES = frozenset(
    {
        TEXT_PLAIN,
        TEXT_LONG_DESC,
        TEXT_IDENTIFIER,
        IMAGE_PNG_BASE64,
        IMAGE_JPEG_BASE64,
    }
)
_METADATA_ORDER: dict[str, int] = {
    TEXT_PLAIN: 0,
    TEXT_LONG_DESC: 1,
    TEXT_IDENTIFIER: 2,
    IMAGE_PNG_BASE64: 3,
    IMAGE_JPEG_BASE64: 4,
}
MAX_PLAIN_TEXT_LENGTH = 256
MAX_LONG_DESCRIPTION_LENGTH = 2048
MAX_IDENTIFIER_LENGTH = 255
MAX_METADATA_IMAGE_BYTES = 100_000
LNURL_PAY_ALLOW_IMAGES = True
_CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_HTML_RE = re.compile(r"<\s*/?\s*(?:html|script|iframe|svg|img|a|body|style|object|embed|form)\b", re.IGNORECASE)
_SECRET_PATTERNS = (
    "access_pass",
    "raw_pass",
    "session_token",
    "bearer ",
    "private_key",
    "issuer_private_key",
    "server_pepper",
    "recovery_phrase",
    "recovery capsule",
    "seed phrase",
    "wallet_seed",
    "bitcoin_seed",
    "mnemonic",
    "xprv",
    "k1=",
    "principal_hash",
    "hmac-sha256:",
    "bbp_",
    "bbk_live_",
    "bbd_live_",
)
_AUTHORITY_CLAIMS = (
    "entitlement active",
    "payment settled",
    "access activated",
    "grants access",
    "authorizes access",
    "role assigned",
    "recovery approved",
)
_PLAN_DISPLAY: dict[PlanCode, str] = {
    PlanCode.LITE: "Lite",
    PlanCode.BASIC: "Basic",
    PlanCode.PLUS: "Plus",
    PlanCode.PRO: "Pro",
    PlanCode.BUSINESS: "Business",
    PlanCode.ENTERPRISE: "Enterprise",
}
_PLAN_DESCRIPTIONS: dict[PlanCode, str] = {
    PlanCode.LITE: "Entry-level access to selected Bitcoin Bastion metrics and public intelligence features.",
    PlanCode.BASIC: "Access to core market, Bitcoin network and selected API metrics within Basic plan limits.",
    PlanCode.PLUS: "Expanded market intelligence, signal and historical-analysis access within Plus plan limits.",
    PlanCode.PRO: "Advanced signals, historical similarity, trace features and API automation within Pro plan limits.",
    PlanCode.BUSINESS: "Business workspace, role-based access and PayRegister-related capabilities within the active Business entitlement.",
    PlanCode.ENTERPRISE: "Enterprise policy, integration and governance capabilities according to the signed Enterprise entitlement.",
}
_PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
_JPEG_MAGIC = b"\xff\xd8\xff"


class LNURLMetadataError(ValueError):
    reason_code = "lnurl_metadata_error"


class MissingPlainTextMetadataError(LNURLMetadataError):
    reason_code = "lnurl_metadata_missing_plain_text"


class DuplicateMetadataTypeError(LNURLMetadataError):
    reason_code = "lnurl_metadata_duplicate_type"


class UnsupportedMetadataTypeError(LNURLMetadataError):
    reason_code = "lnurl_metadata_unsupported_type"


class MetadataValueTooLongError(LNURLMetadataError):
    reason_code = "lnurl_metadata_value_too_long"


class UnsafeMetadataContentError(LNURLMetadataError):
    reason_code = "lnurl_metadata_unsafe_content"


class InvalidLightningIdentifierError(LNURLMetadataError):
    reason_code = "lnurl_metadata_invalid_identifier"


class InvalidMetadataImageError(LNURLMetadataError):
    reason_code = "lnurl_metadata_invalid_image"


class MetadataImageTooLargeError(LNURLMetadataError):
    reason_code = "lnurl_metadata_image_too_large"


@dataclass(frozen=True, slots=True)
class LNURLPayMetadataEntry:
    mime_type: str
    value: str


@dataclass(frozen=True, slots=True)
class LNURLMetadataImage:
    mime_type: str
    base64_data: str


@dataclass(frozen=True, slots=True)
class LNURLPayMetadataResult:
    entries: tuple[LNURLPayMetadataEntry, ...]
    canonical_json: str
    metadata_hash: str
    plain_text: str
    identifier: str | None


class LNURLPayMetadataBuilder:
    allowed_mime_types: ClassVar[frozenset[str]] = ALLOWED_LNURL_PAY_METADATA_TYPES

    def __init__(
        self,
        *,
        max_plain_text_length: int = MAX_PLAIN_TEXT_LENGTH,
        max_long_description_length: int = MAX_LONG_DESCRIPTION_LENGTH,
        max_identifier_length: int = MAX_IDENTIFIER_LENGTH,
        max_image_bytes: int = MAX_METADATA_IMAGE_BYTES,
        allow_images: bool = LNURL_PAY_ALLOW_IMAGES,
    ) -> None:
        self.max_plain_text_length = max_plain_text_length
        self.max_long_description_length = max_long_description_length
        self.max_identifier_length = max_identifier_length
        self.max_image_bytes = max_image_bytes
        self.allow_images = allow_images

    def build_subscription_metadata(
        self,
        *,
        plan_code: str,
        duration_label: str,
        product_name: str | None = None,
        description: str | None = None,
        lightning_identifier: str | None = None,
        image: LNURLMetadataImage | None = None,
    ) -> LNURLPayMetadataResult:
        try:
            plan = normalize_plan_code(plan_code)
        except InvalidPlanCodeError as exc:
            raise LNURLMetadataError("Unknown subscription plan for LNURL-pay metadata") from exc
        label = _PLAN_DISPLAY[plan]
        product = _normalize_text(product_name or "Bitcoin Bastion", max_length=80, field="product_name")
        duration = _normalize_text(duration_label, max_length=80, field="duration_label")
        plain = f"{product} {label} Pass — {duration}"
        long_desc = description if description is not None else _PLAN_DESCRIPTIONS[plan]
        return self.build_custom_metadata(plain_text=plain, long_description=long_desc, identifier=lightning_identifier, image=image)

    def build_payregister_metadata(
        self,
        *,
        merchant_display_name: str,
        order_reference: str | None,
        terminal_reference: str | None,
        description: str | None,
        lightning_identifier: str | None = None,
        image: LNURLMetadataImage | None = None,
    ) -> LNURLPayMetadataResult:
        merchant = _normalize_text(merchant_display_name, max_length=80, field="merchant_display_name")
        order = _normalize_public_reference(order_reference, label="order_reference")
        terminal = _normalize_public_reference(terminal_reference, label="terminal_reference")
        plain = f"Payment to {merchant}"
        if order:
            plain = f"{plain} — Order {order}"
        details = []
        if terminal:
            details.append(f"Terminal {terminal}")
        if description:
            details.append(_normalize_text(description, max_length=512, field="description"))
        long_desc = ", ".join(details) if details else None
        return self.build_custom_metadata(plain_text=plain, long_description=long_desc, identifier=lightning_identifier, image=image)

    def build_custom_metadata(
        self,
        *,
        plain_text: str,
        long_description: str | None = None,
        identifier: str | None = None,
        image: LNURLMetadataImage | None = None,
    ) -> LNURLPayMetadataResult:
        entries = [LNURLPayMetadataEntry(TEXT_PLAIN, _normalize_text(plain_text, max_length=self.max_plain_text_length, field="text/plain"))]
        if long_description is not None:
            entries.append(LNURLPayMetadataEntry(TEXT_LONG_DESC, _normalize_text(long_description, max_length=self.max_long_description_length, field="text/long-desc")))
        if identifier is not None:
            entries.append(LNURLPayMetadataEntry(TEXT_IDENTIFIER, validate_lightning_identifier(identifier, max_length=self.max_identifier_length)))
        if image is not None:
            entries.append(self._validate_image(image))
        return self.canonicalize(entries)

    def canonicalize(self, entries: list[LNURLPayMetadataEntry] | tuple[LNURLPayMetadataEntry, ...]) -> LNURLPayMetadataResult:
        if not entries:
            raise MissingPlainTextMetadataError("LNURL-pay metadata requires text/plain")
        normalized: list[LNURLPayMetadataEntry] = []
        seen: set[str] = set()
        for entry in entries:
            if entry.mime_type not in self.allowed_mime_types:
                raise UnsupportedMetadataTypeError("Unsupported LNURL-pay metadata MIME type")
            if entry.mime_type in seen:
                raise DuplicateMetadataTypeError("Duplicate LNURL-pay metadata MIME type")
            seen.add(entry.mime_type)
            normalized.append(self._normalize_entry(entry))
        plain_entries = [entry for entry in normalized if entry.mime_type == TEXT_PLAIN]
        if len(plain_entries) != 1:
            raise MissingPlainTextMetadataError("LNURL-pay metadata requires exactly one text/plain entry")
        ordered = tuple(sorted(normalized, key=lambda item: _METADATA_ORDER[item.mime_type]))
        canonical = json.dumps([[entry.mime_type, entry.value] for entry in ordered], ensure_ascii=False, separators=(",", ":"), allow_nan=False)
        return LNURLPayMetadataResult(
            entries=ordered,
            canonical_json=canonical,
            metadata_hash=sha256_prefixed(canonical),
            plain_text=plain_entries[0].value,
            identifier=next((entry.value for entry in ordered if entry.mime_type == TEXT_IDENTIFIER), None),
        )

    def _normalize_entry(self, entry: LNURLPayMetadataEntry) -> LNURLPayMetadataEntry:
        if entry.mime_type == TEXT_PLAIN:
            return LNURLPayMetadataEntry(entry.mime_type, _normalize_text(entry.value, max_length=self.max_plain_text_length, field="text/plain"))
        if entry.mime_type == TEXT_LONG_DESC:
            return LNURLPayMetadataEntry(entry.mime_type, _normalize_text(entry.value, max_length=self.max_long_description_length, field="text/long-desc"))
        if entry.mime_type == TEXT_IDENTIFIER:
            return LNURLPayMetadataEntry(entry.mime_type, validate_lightning_identifier(entry.value, max_length=self.max_identifier_length))
        if entry.mime_type in {IMAGE_PNG_BASE64, IMAGE_JPEG_BASE64}:
            return self._validate_image(LNURLMetadataImage(entry.mime_type, entry.value))
        raise UnsupportedMetadataTypeError("Unsupported LNURL-pay metadata MIME type")

    def _validate_image(self, image: LNURLMetadataImage) -> LNURLPayMetadataEntry:
        if not self.allow_images:
            raise InvalidMetadataImageError("LNURL-pay metadata images are disabled")
        if image.mime_type not in {IMAGE_PNG_BASE64, IMAGE_JPEG_BASE64}:
            raise InvalidMetadataImageError("Unsupported LNURL-pay metadata image type")
        if image.base64_data.strip().lower().startswith(("data:", "http://", "https://")):
            raise InvalidMetadataImageError("LNURL-pay image metadata must be raw base64")
        try:
            decoded = base64.b64decode(image.base64_data, validate=True)
        except (binascii.Error, ValueError) as exc:
            raise InvalidMetadataImageError("Invalid LNURL-pay image base64") from exc
        if len(decoded) > self.max_image_bytes:
            raise MetadataImageTooLargeError("LNURL-pay metadata image is too large")
        if decoded.lstrip().startswith(b"<svg"):
            raise InvalidMetadataImageError("SVG is not supported in LNURL-pay metadata")
        if image.mime_type == IMAGE_PNG_BASE64 and not decoded.startswith(_PNG_MAGIC):
            raise InvalidMetadataImageError("PNG metadata magic bytes do not match")
        if image.mime_type == IMAGE_JPEG_BASE64 and not decoded.startswith(_JPEG_MAGIC):
            raise InvalidMetadataImageError("JPEG metadata magic bytes do not match")
        return LNURLPayMetadataEntry(image.mime_type, image.base64_data.strip())


def validate_lightning_identifier(identifier: str, *, max_length: int = MAX_IDENTIFIER_LENGTH) -> str:
    try:
        value = _normalize_text(identifier, max_length=max_length, field="text/identifier")
    except UnsafeMetadataContentError as exc:
        raise InvalidLightningIdentifierError("Invalid Lightning identifier") from exc
    if "//" in value or ":" in value or "?" in value or "#" in value or "/" in value or "@" not in value:
        raise InvalidLightningIdentifierError("Invalid Lightning identifier")
    if value.count("@") != 1:
        raise InvalidLightningIdentifierError("Invalid Lightning identifier")
    local, domain = value.split("@", 1)
    if not local or not domain or len(local) > 64 or len(domain) > 190:
        raise InvalidLightningIdentifierError("Invalid Lightning identifier")
    if any(ch.isspace() for ch in value) or _CONTROL_RE.search(value):
        raise InvalidLightningIdentifierError("Invalid Lightning identifier")
    parsed = urlparse(f"//{domain}")
    host = (parsed.hostname or "").lower().rstrip(".")
    if not host or parsed.username or parsed.password or host in {"localhost", "127.0.0.1"}:
        raise InvalidLightningIdentifierError("Invalid Lightning identifier")
    if not re.fullmatch(r"[a-z0-9](?:[a-z0-9.-]{0,188}[a-z0-9])?", host):
        raise InvalidLightningIdentifierError("Invalid Lightning identifier")
    return f"{local.lower()}@{host}"


def metadata_result_from_json(metadata_json: str) -> LNURLPayMetadataResult:
    try:
        decoded = json.loads(metadata_json)
    except json.JSONDecodeError as exc:
        raise LNURLMetadataError("Invalid LNURL-pay metadata JSON") from exc
    if not isinstance(decoded, list):
        raise LNURLMetadataError("LNURL-pay metadata must be an array")
    entries: list[LNURLPayMetadataEntry] = []
    for item in decoded:
        if not isinstance(item, list) or len(item) != 2 or not isinstance(item[0], str) or not isinstance(item[1], str):
            raise LNURLMetadataError("LNURL-pay metadata entries must be two-item string arrays")
        entries.append(LNURLPayMetadataEntry(item[0], item[1]))
    return LNURLPayMetadataBuilder().canonicalize(entries)


def _normalize_text(value: str, *, max_length: int, field: str) -> str:
    if not isinstance(value, str):
        raise UnsafeMetadataContentError("LNURL-pay metadata value must be text")
    normalized = " ".join(value.replace("\r", " ").replace("\n", " ").split())
    if not normalized:
        raise MissingPlainTextMetadataError("LNURL-pay text metadata must not be empty")
    if len(normalized) > max_length:
        raise MetadataValueTooLongError("LNURL-pay metadata value is too long")
    lowered = normalized.lower()
    if _CONTROL_RE.search(normalized) or _HTML_RE.search(normalized) or "javascript:" in lowered:
        raise UnsafeMetadataContentError("LNURL-pay metadata contains active or control content")
    if any(pattern in lowered for pattern in _SECRET_PATTERNS):
        raise UnsafeMetadataContentError("LNURL-pay metadata contains a forbidden secret pattern")
    if field == TEXT_LONG_DESC and any(claim in lowered for claim in _AUTHORITY_CLAIMS):
        raise UnsafeMetadataContentError("LNURL-pay metadata must not claim authorization or settlement")
    return normalized


def _normalize_public_reference(value: str | None, *, label: str) -> str | None:
    if value is None:
        return None
    text = _normalize_text(value, max_length=80, field=label)
    lowered = text.lower()
    if lowered.startswith(("id:", "db:", "internal:", "user:", "customer:")):
        raise UnsafeMetadataContentError("LNURL-pay metadata public reference is unsafe")
    return text


__all__ = [
    "ALLOWED_LNURL_PAY_METADATA_TYPES",
    "DuplicateMetadataTypeError",
    "IMAGE_JPEG_BASE64",
    "IMAGE_PNG_BASE64",
    "InvalidLightningIdentifierError",
    "InvalidMetadataImageError",
    "LNURLMetadataError",
    "LNURLMetadataImage",
    "LNURLPayMetadataBuilder",
    "LNURLPayMetadataEntry",
    "LNURLPayMetadataResult",
    "MAX_IDENTIFIER_LENGTH",
    "MAX_LONG_DESCRIPTION_LENGTH",
    "MAX_METADATA_IMAGE_BYTES",
    "MAX_PLAIN_TEXT_LENGTH",
    "MetadataImageTooLargeError",
    "MetadataValueTooLongError",
    "MissingPlainTextMetadataError",
    "TEXT_IDENTIFIER",
    "TEXT_LONG_DESC",
    "TEXT_PLAIN",
    "UnsupportedMetadataTypeError",
    "UnsafeMetadataContentError",
    "metadata_result_from_json",
    "validate_lightning_identifier",
]
