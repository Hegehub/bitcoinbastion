"""Production LNURL-pay commentAllowed and comment handling boundary."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import StrEnum
import html
import re
import unicodedata
from typing import Any
from urllib.parse import unquote_plus

from app.services.access.crypto.hashing import sha256_prefixed

LNURL_COMMENT_ALLOWED_DEFAULT = 0
LNURL_COMMENT_GLOBAL_MAX_CHARS = 280
LNURL_COMMENT_GLOBAL_MAX_BYTES = 2048
LNURL_COMMENT_RETENTION_DAYS = 7
_INPUT_TRUST = "untrusted_external_metadata"
_CONTROL_RE = re.compile(r"[\x00-\x1f\x7f]")
_PERCENT_ESCAPE_RE = re.compile(r"%[0-9a-fA-F]{2}")
_DANGEROUS_TERMS = (
    "access_pass",
    "session_token",
    "private_key",
    "wallet_seed",
    "bitcoin_seed",
    "seed phrase",
    "mnemonic",
    "xprv",
    "preimage",
    "grant access",
    "grants access",
    "upgrade me",
    "enterprise",
    "approve refund",
    "approve withdraw",
    "bypass step-up",
    "complete recovery",
)
_BIDI_OR_ZERO_WIDTH = frozenset({"\u200b", "\u200c", "\u200d", "\u2060", "\u202a", "\u202b", "\u202c", "\u202d", "\u202e"})


class LNURLCommentStorageMode(StrEnum):
    NONE = "none"
    HASH_ONLY = "hash_only"
    ENCRYPTED = "encrypted"


class LNURLCommentClassification(StrEnum):
    MERCHANT_NOTE = "merchant_note"
    ORDER_REFERENCE = "order_reference"
    RECEIPT_NOTE = "receipt_note"
    SUPPORT_REFERENCE = "support_reference"
    GENERAL_UNTRUSTED_TEXT = "general_untrusted_text"


@dataclass(frozen=True, slots=True)
class LNURLCommentConfig:
    default_allowed_chars: int = LNURL_COMMENT_ALLOWED_DEFAULT
    global_max_chars: int = LNURL_COMMENT_GLOBAL_MAX_CHARS
    global_max_bytes: int = LNURL_COMMENT_GLOBAL_MAX_BYTES
    storage_enabled: bool = False
    retention_days: int = LNURL_COMMENT_RETENTION_DAYS
    allow_control_characters: bool = False


@dataclass(frozen=True, slots=True)
class LNURLCommentContext:
    flow_type: str = "subscription_checkout"
    product_max_chars: int | None = None
    merchant_max_chars: int | None = None
    terminal_max_chars: int | None = None
    request_max_chars: int | None = None
    classification: LNURLCommentClassification | None = None
    storage_requested: bool = False


@dataclass(frozen=True, slots=True)
class ValidatedLNURLComment:
    present: bool
    normalized_comment: str | None
    comment_hash: str | None
    character_count: int
    allowed_character_count: int
    storage_mode: LNURLCommentStorageMode
    classification: LNURLCommentClassification
    input_trust: str = _INPUT_TRUST
    suspicious_text_flags: tuple[str, ...] = field(default_factory=tuple)
    retention_expires_at: datetime | None = None


class LNURLCommentError(ValueError):
    reason_code = "comment_invalid"

    def __init__(self, message: str | None = None, *, reason_code: str | None = None) -> None:
        self.reason_code = reason_code or self.reason_code
        super().__init__(message or self.reason_code)


class LNURLCommentNotAllowedError(LNURLCommentError):
    reason_code = "comment_not_allowed"


class LNURLCommentTooLongError(LNURLCommentError):
    reason_code = "comment_too_long"


class LNURLCommentInvalidEncodingError(LNURLCommentError):
    reason_code = "comment_invalid_encoding"


class LNURLCommentForbiddenCharactersError(LNURLCommentError):
    reason_code = "comment_contains_forbidden_characters"


class LNURLCommentConfigurationError(LNURLCommentError):
    reason_code = "comment_configuration_invalid"


class LNURLCommentService:
    """Validate, normalize, hash, redact, and classify untrusted LNURL comments only."""

    def __init__(self, config: LNURLCommentConfig | None = None) -> None:
        self.config = config or LNURLCommentConfig()
        self.validate_comment_allowed(self.config.default_allowed_chars)
        self.validate_comment_allowed(self.config.global_max_chars)
        if self.config.global_max_bytes <= 0 or self.config.retention_days < 0:
            raise LNURLCommentConfigurationError()

    def resolve_comment_limit(self, context: LNURLCommentContext | None = None) -> int:
        ctx = context or LNURLCommentContext(request_max_chars=self.config.default_allowed_chars)
        limits = [self.config.global_max_chars]
        for value in (ctx.product_max_chars, ctx.merchant_max_chars, ctx.terminal_max_chars, ctx.request_max_chars):
            if value is None:
                return 0
            limits.append(self.validate_comment_allowed(value))
        return min(limits) if limits else 0

    def validate_comment_allowed(self, comment_allowed: int) -> int:
        if not isinstance(comment_allowed, int) or isinstance(comment_allowed, bool):
            raise LNURLCommentConfigurationError()
        if comment_allowed < 0:
            raise LNURLCommentConfigurationError()
        if comment_allowed > self.config.global_max_chars:
            raise LNURLCommentConfigurationError()
        return comment_allowed

    def validate_comment(self, comment: str | None, allowed_chars: int, *, context: LNURLCommentContext | None = None) -> ValidatedLNURLComment:
        allowed = self.validate_comment_allowed(allowed_chars)
        classification = (context.classification if context and context.classification else self._classify(context))
        if comment is None or comment == "":
            return ValidatedLNURLComment(False, None, None, 0, allowed, LNURLCommentStorageMode.NONE, classification)
        if allowed <= 0:
            raise LNURLCommentNotAllowedError()
        if not isinstance(comment, str):
            raise LNURLCommentInvalidEncodingError()
        if len(comment.encode("utf-8", "surrogatepass")) > self.config.global_max_bytes:
            raise LNURLCommentTooLongError()
        decoded = self._decode_once(comment)
        if len(decoded.encode("utf-8", "surrogatepass")) > self.config.global_max_bytes:
            raise LNURLCommentTooLongError()
        normalized = self.normalize_comment(decoded)
        if len(normalized) > allowed or len(decoded) > allowed:
            raise LNURLCommentTooLongError()
        flags = self._suspicious_flags(normalized)
        mode = LNURLCommentStorageMode.ENCRYPTED if self.should_store_raw_comment(context) else LNURLCommentStorageMode.HASH_ONLY
        return ValidatedLNURLComment(
            True,
            normalized,
            self.compute_comment_hash(normalized),
            len(normalized),
            allowed,
            mode,
            classification,
            suspicious_text_flags=flags,
            retention_expires_at=datetime.now(UTC) + timedelta(days=self.config.retention_days),
        )

    def normalize_comment(self, comment: str) -> str:
        if "\x00" in comment or "\r" in comment or "\n" in comment:
            raise LNURLCommentForbiddenCharactersError()
        if not self.config.allow_control_characters and _CONTROL_RE.search(comment):
            raise LNURLCommentForbiddenCharactersError()
        try:
            normalized = unicodedata.normalize("NFC", comment)
        except TypeError as exc:
            raise LNURLCommentInvalidEncodingError() from exc
        if not normalized.strip():
            return ""
        return normalized.strip()

    def compute_comment_hash(self, comment: str) -> str:
        return sha256_prefixed(unicodedata.normalize("NFC", comment))

    def redact_comment(self, comment: str) -> str:
        normalized = self.normalize_comment(self._decode_once(comment))
        if not normalized:
            return ""
        escaped = html.escape(normalized, quote=True)
        return escaped if len(escaped) <= 24 else f"{escaped[:12]}…{escaped[-8:]}"

    def build_comment_audit_metadata(self, validated_comment: ValidatedLNURLComment) -> dict[str, Any]:
        return {
            "comment_present": validated_comment.present,
            "comment_hash": validated_comment.comment_hash,
            "character_count": validated_comment.character_count,
            "effective_limit": validated_comment.allowed_character_count,
            "storage_mode": validated_comment.storage_mode.value,
            "classification": validated_comment.classification.value,
            "input_trust": validated_comment.input_trust,
            "suspicious_text_flags": list(validated_comment.suspicious_text_flags),
        }

    def should_store_raw_comment(self, context: LNURLCommentContext | None) -> bool:
        return bool(self.config.storage_enabled and context and context.storage_requested)

    def _decode_once(self, comment: str) -> str:
        try:
            decoded = unquote_plus(comment, errors="strict") if "%" in comment or "+" in comment else comment
        except UnicodeDecodeError as exc:
            raise LNURLCommentInvalidEncodingError() from exc
        if _PERCENT_ESCAPE_RE.search(decoded):
            raise LNURLCommentInvalidEncodingError()
        return decoded

    def _classify(self, context: LNURLCommentContext | None) -> LNURLCommentClassification:
        flow = (context.flow_type if context else "").lower()
        if "payregister" in flow or "merchant" in flow:
            return LNURLCommentClassification.MERCHANT_NOTE
        if "receipt" in flow:
            return LNURLCommentClassification.RECEIPT_NOTE
        return LNURLCommentClassification.GENERAL_UNTRUSTED_TEXT

    def _suspicious_flags(self, value: str) -> tuple[str, ...]:
        flags: list[str] = []
        lowered = value.lower()
        if any(term in lowered for term in _DANGEROUS_TERMS):
            flags.append("dangerous_semantic_request")
        if any(char in value for char in _BIDI_OR_ZERO_WIDTH):
            flags.append("display_sensitive_unicode")
        if "ignore previous" in lowered or "system prompt" in lowered or "developer instruction" in lowered:
            flags.append("prompt_injection_like_text")
        if "<script" in lowered or "javascript:" in lowered:
            flags.append("html_script_like_text")
        return tuple(flags)
