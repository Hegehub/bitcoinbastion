"""Structured Bastion Auth Intent primitives.

This module is pure and deterministic. It builds, renders, validates, hashes, and
redacts wallet/LNURL policy intents; it does not verify Bitcoin signatures,
LNURL callbacks, payments, policy decisions, audit events, or revocation state.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any, Mapping

from app.domain.wallet_auth.actions import CRITICAL_WALLET_ACTIONS, WalletAuthAction
from app.domain.wallet_auth.constants import (
    DEDICATED_AUTH_ADDRESS_WARNING,
    FORBIDDEN_WALLET_SECRET_TERMS,
    REQUIRED_SIGNATURE_WARNING,
    WALLET_AUTH_INTENT_TYPE,
    WALLET_AUTH_INTENT_VERSION,
)
from app.domain.wallet_auth.risks import WalletRiskLevel
from app.services.wallet_auth.privacy_commitments import redact_sensitive_auth_material

WALLET_HUMAN_INTENT_TYPE = "bastion_wallet_human_intent"
LNURL_POLICY_INTENT_TYPE = "bastion_lnurl_policy_intent"
LNURL_AUTH_WARNING = (
    "LNURL-auth proves control of a Lightning wallet linking key for this domain. "
    "It is not proof of on-chain treasury ownership and does not authorize a Bitcoin transaction."
)
HIGH_RISK_APPROVAL_WARNING = (
    "This approval is limited to the action, scopes, expiry, and policy context shown here. "
    "It does not grant unrestricted access."
)
_SUPPORTED_INTENT_TYPES = {WALLET_AUTH_INTENT_TYPE, WALLET_HUMAN_INTENT_TYPE, LNURL_POLICY_INTENT_TYPE}
_MAX_INTENT_TTL = timedelta(days=7)
_HASH_PREFIXES = ("sha256:", "hmac-sha256:")
_SECRET_VALUE_RE = re.compile(
    r"\b(seed phrase|wallet seed|bitcoin seed|mnemonic|private[_ -]?key|xprv|yprv|zprv)\b",
    re.IGNORECASE,
)
_SENSITIVE_FIELD_RE = re.compile(r"(signature|raw_k1|\bk1\b|session_token|access_pass|recovery|private_key|seed|mnemonic|xprv)", re.I)


@dataclass(frozen=True)
class BastionAuthIntent:
    type: str = WALLET_AUTH_INTENT_TYPE
    version: int = WALLET_AUTH_INTENT_VERSION
    domain: str = ""
    action: str = ""
    purpose: str = ""
    origin: str = ""
    network: str = ""
    challenge_id: str = ""
    nonce: str = ""
    device_key_fingerprint: str = ""
    policy_hash: str = ""
    risk_level: str = ""
    issued_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    expires_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    wallet_proof_type: str = ""
    verification_strength_hint: str = "standard"
    requested_scopes: tuple[str, ...] = ()
    principal_hint_hash: str | None = None
    access_certificate_hint: str | None = None
    warnings: tuple[str, ...] = (REQUIRED_SIGNATURE_WARNING, DEDICATED_AUTH_ADDRESS_WARNING)


@dataclass(frozen=True)
class BastionHumanIntent:
    type: str = WALLET_HUMAN_INTENT_TYPE
    version: int = WALLET_AUTH_INTENT_VERSION
    domain: str = ""
    action: str = ""
    purpose: str = ""
    network: str | None = None
    challenge_id: str = ""
    nonce: str = ""
    principal_hash: str | None = None
    device_key_fingerprint: str = ""
    session_hash: str | None = None
    policy_hash: str = ""
    risk_level: str = ""
    requested_scopes: tuple[str, ...] = ()
    requested_metric_groups: tuple[str, ...] = ()
    expires_in_seconds: int | None = None
    cannot_access: tuple[str, ...] = ()
    object_reference_hash: str | None = None
    business_role: str | None = None
    payregister_context_hash: str | None = None
    recovery_context_hash: str | None = None
    issued_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    expires_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    warnings: tuple[str, ...] = (REQUIRED_SIGNATURE_WARNING, DEDICATED_AUTH_ADDRESS_WARNING, HIGH_RISK_APPROVAL_WARNING)


@dataclass(frozen=True)
class BastionLNURLPolicyIntent:
    type: str = LNURL_POLICY_INTENT_TYPE
    version: int = WALLET_AUTH_INTENT_VERSION
    domain: str = ""
    lnurl_auth_domain: str = ""
    action: str = ""
    lnurl_action: str = ""
    k1_hash: str = ""
    purpose: str = ""
    challenge_id: str = ""
    device_key_fingerprint: str | None = None
    principal_hint_hash: str | None = None
    policy_hash: str = ""
    risk_level: str = ""
    issued_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    expires_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    allowed_callback_host: str = ""
    required_policy_decision: str = ""
    warnings: tuple[str, ...] = (LNURL_AUTH_WARNING, HIGH_RISK_APPROVAL_WARNING)


@dataclass(frozen=True)
class IntentValidationResult:
    valid: bool
    errors: tuple[str, ...] = ()


@dataclass(frozen=True)
class IntentRenderResult:
    rendered: str
    intent_hash: str


def _as_dict(intent: Mapping[str, Any] | object) -> dict[str, Any]:
    if dataclasses.is_dataclass(intent) and not isinstance(intent, type):
        return dataclasses.asdict(intent)
    if isinstance(intent, Mapping):
        return dict(intent)
    raise TypeError("intent must be a dataclass instance or mapping")


def _normalize_datetime(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _json_default(value: Any) -> Any:
    if isinstance(value, datetime):
        return _normalize_datetime(value)
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, tuple):
        return list(value)
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def canonical_intent_json(intent: Mapping[str, Any]) -> str:
    return json.dumps(intent, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=_json_default, allow_nan=False)


def hash_intent(intent: Mapping[str, Any]) -> str:
    payload = canonical_intent_json(intent).encode("utf-8")
    return f"sha256:{hashlib.sha256(payload).hexdigest()}"


def render_wallet_message(intent: BastionAuthIntent | BastionHumanIntent) -> str:
    data = _as_dict(intent)
    if data.get("type") not in {WALLET_AUTH_INTENT_TYPE, WALLET_HUMAN_INTENT_TYPE}:
        raise ValueError("wallet message can only render wallet auth or human intents")
    lines = [
        "Bastion Wallet Proof Auth",
        "",
        f"Version: {data['version']}",
        f"Domain: {data['domain']}",
        f"Action: {data['action']}",
        f"Purpose: {data['purpose']}",
        f"Origin: {data.get('origin') or 'not_applicable'}",
        f"Network: {data.get('network') or 'not_applicable'}",
        f"Challenge ID: {data['challenge_id']}",
        f"Nonce: {data['nonce']}",
        f"Device key fingerprint: {data['device_key_fingerprint']}",
        f"Policy hash: {data['policy_hash']}",
        f"Risk: {data['risk_level']}",
        f"Requested scopes: {', '.join(data.get('requested_scopes') or []) or 'none'}",
        f"Issued at: {_format_dt(data['issued_at'])}",
        f"Expires at: {_format_dt(data['expires_at'])}",
    ]
    if data.get("type") == WALLET_HUMAN_INTENT_TYPE:
        lines.extend(
            [
                f"Requested scopes: {', '.join(data.get('requested_scopes') or []) or 'none'}",
                f"Requested metric groups: {', '.join(data.get('requested_metric_groups') or []) or 'none'}",
                f"Cannot access: {', '.join(data.get('cannot_access') or []) or 'none'}",
            ]
        )
        for label, key in (
            ("Object reference hash", "object_reference_hash"),
            ("Business role", "business_role"),
            ("PayRegister context hash", "payregister_context_hash"),
            ("Recovery context hash", "recovery_context_hash"),
        ):
            if data.get(key):
                lines.append(f"{label}: {data[key]}")
    lines.extend(["", REQUIRED_SIGNATURE_WARNING])
    if HIGH_RISK_APPROVAL_WARNING in data.get("warnings", ()): 
        lines.append(HIGH_RISK_APPROVAL_WARNING)
    message = "\n".join(lines)
    _reject_forbidden_values(message)
    if message.strip().lower() == "login" or len(message.strip()) < 80:
        raise ValueError("wallet message is ambiguous")
    return message


def render_lnurl_policy_context(intent: BastionLNURLPolicyIntent) -> dict[str, Any]:
    data = _as_dict(intent)
    allowed_keys = {
        "type", "version", "domain", "lnurl_auth_domain", "action", "lnurl_action", "k1_hash", "purpose",
        "challenge_id", "device_key_fingerprint", "policy_hash", "risk_level", "issued_at", "expires_at",
        "required_policy_decision", "warnings",
    }
    return {key: _safe_value(data[key]) for key in allowed_keys if key in data}


def build_wallet_auth_intent(**kwargs: Any) -> BastionAuthIntent:
    if "requested_scopes" in kwargs:
        kwargs["requested_scopes"] = tuple(kwargs["requested_scopes"])
    intent = BastionAuthIntent(**kwargs, warnings=(REQUIRED_SIGNATURE_WARNING, DEDICATED_AUTH_ADDRESS_WARNING))
    _raise_if_invalid(intent)
    return intent


def build_human_intent(**kwargs: Any) -> BastionHumanIntent:
    if "requested_scopes" in kwargs:
        kwargs["requested_scopes"] = tuple(kwargs["requested_scopes"])
    if "requested_metric_groups" in kwargs:
        kwargs["requested_metric_groups"] = tuple(kwargs["requested_metric_groups"])
    if "cannot_access" in kwargs:
        kwargs["cannot_access"] = tuple(kwargs["cannot_access"])
    if kwargs.get("expires_in_seconds") is None and kwargs.get("issued_at") and kwargs.get("expires_at"):
        kwargs["expires_in_seconds"] = int((kwargs["expires_at"] - kwargs["issued_at"]).total_seconds())
    intent = BastionHumanIntent(**kwargs)
    _raise_if_invalid(intent)
    return intent


def build_lnurl_policy_intent(**kwargs: Any) -> BastionLNURLPolicyIntent:
    intent = BastionLNURLPolicyIntent(**kwargs)
    _raise_if_invalid(intent)
    return intent


def validate_intent(intent: Mapping[str, Any] | object) -> IntentValidationResult:
    errors: list[str] = []
    try:
        data = _as_dict(intent)
    except TypeError as exc:
        return IntentValidationResult(False, (str(exc),))
    intent_type = data.get("type")
    if intent_type not in _SUPPORTED_INTENT_TYPES:
        errors.append("unknown intent type")
    if data.get("version") != WALLET_AUTH_INTENT_VERSION:
        errors.append("unsupported intent version")
    for key in ("domain", "action", "purpose", "policy_hash", "risk_level"):
        if not str(data.get(key) or "").strip():
            errors.append(f"missing {key}")
    if str(data.get("policy_hash") or "").strip() and not str(data["policy_hash"]).startswith(_HASH_PREFIXES):
        errors.append("policy_hash must use a supported hash prefix")
    try:
        WalletRiskLevel(str(data.get("risk_level")))
    except ValueError:
        errors.append("invalid risk_level")
    if intent_type in {WALLET_AUTH_INTENT_TYPE, WALLET_HUMAN_INTENT_TYPE}:
        for key in ("challenge_id", "nonce", "device_key_fingerprint"):
            if not str(data.get(key) or "").strip():
                errors.append(f"missing {key}")
        warnings = tuple(data.get("warnings") or ())
        if REQUIRED_SIGNATURE_WARNING not in warnings:
            errors.append("missing wallet safety warning")
        if intent_type == WALLET_AUTH_INTENT_TYPE and requires_human_intent(str(data.get("action") or ""), str(data.get("risk_level") or "")):
            errors.append("critical action requires human intent")
    if intent_type == LNURL_POLICY_INTENT_TYPE:
        for key in ("lnurl_auth_domain", "lnurl_action", "k1_hash", "allowed_callback_host", "required_policy_decision"):
            if not str(data.get(key) or "").strip():
                errors.append(f"missing {key}")
        if "sha256:" not in str(data.get("k1_hash") or ""):
            errors.append("k1_hash must be a hash commitment")
        if LNURL_AUTH_WARNING not in tuple(data.get("warnings") or ()): 
            errors.append("missing LNURL safety warning")
    issued_at = data.get("issued_at")
    expires_at = data.get("expires_at")
    if expires_at is None:
        errors.append("missing expires_at")
    if issued_at is None:
        errors.append("missing issued_at")
    if isinstance(issued_at, datetime) and isinstance(expires_at, datetime):
        issued = _aware(issued_at)
        expires = _aware(expires_at)
        if issued >= expires:
            errors.append("issued_at must be before expires_at")
        if expires - issued > _MAX_INTENT_TTL:
            errors.append("expires_at is unreasonably far in the future")
    _validate_no_forbidden_names_or_values(data, errors)
    return IntentValidationResult(not errors, tuple(errors))


def is_expired(intent: Mapping[str, Any] | object, now: datetime) -> bool:
    data = _as_dict(intent)
    expires_at = data.get("expires_at")
    if not isinstance(expires_at, datetime):
        return True
    return _aware(now) >= _aware(expires_at)


def assert_not_expired(intent: Mapping[str, Any] | object, now: datetime) -> None:
    if is_expired(intent, now):
        raise ValueError("intent expired")


def is_critical_action(action: str) -> bool:
    try:
        return WalletAuthAction(action) in CRITICAL_WALLET_ACTIONS
    except ValueError:
        return action in {"recovery_change"}


def requires_human_intent(action: str, risk_level: str) -> bool:
    try:
        risk = WalletRiskLevel(risk_level)
    except ValueError:
        return True
    if risk == WalletRiskLevel.CRITICAL:
        return True
    return risk == WalletRiskLevel.HIGH and is_critical_action(action)


def redact_intent_for_logs(intent: Mapping[str, Any] | object) -> dict[str, Any]:
    redacted = _redact_mapping(_as_dict(intent))
    if not isinstance(redacted, dict):
        raise TypeError("redacted intent must be a mapping")
    return redacted


def _raise_if_invalid(intent: Mapping[str, Any] | object) -> None:
    result = validate_intent(intent)
    if not result.valid:
        raise ValueError("invalid intent: " + "; ".join(result.errors))


def _format_dt(value: Any) -> str:
    if isinstance(value, datetime):
        return _normalize_datetime(value)
    return str(value)


def _aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _safe_value(value: Any) -> Any:
    if isinstance(value, datetime):
        return _normalize_datetime(value)
    if isinstance(value, tuple):
        return list(value)
    return value


def _validate_no_forbidden_names_or_values(value: Any, errors: list[str], path: str = "intent") -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = str(key)
            if key_text.lower() in FORBIDDEN_WALLET_SECRET_TERMS:
                errors.append(f"forbidden secret field at {path}")
            _validate_no_forbidden_names_or_values(item, errors, f"{path}.{key_text}")
    elif isinstance(value, (list, tuple, set)):
        for index, item in enumerate(value):
            _validate_no_forbidden_names_or_values(item, errors, f"{path}[{index}]")
    elif isinstance(value, str) and _SECRET_VALUE_RE.search(value):
        # Required warnings contain the word seed/private in safety copy and are allowed.
        if value not in {REQUIRED_SIGNATURE_WARNING, DEDICATED_AUTH_ADDRESS_WARNING, LNURL_AUTH_WARNING, HIGH_RISK_APPROVAL_WARNING}:
            errors.append(f"forbidden secret-like value at {path}")


def _reject_forbidden_values(message: str) -> None:
    unsafe = ("xprv", "private_key", "mnemonic", "wallet_seed")
    if any(term in message.lower() for term in unsafe):
        raise ValueError("wallet message contains forbidden secret-like material")


def _redact_mapping(value: Any) -> Any:
    if isinstance(value, Mapping):
        redacted: dict[str, Any] = {}
        for key, item in value.items():
            key_text = str(key)
            if _SENSITIVE_FIELD_RE.search(key_text):
                if key_text in {"policy_hash", "principal_hash", "session_hash", "k1_hash", "challenge_id"}:
                    redacted[key_text] = _safe_value(item)
                else:
                    redacted[key_text] = "<redacted>"
            else:
                redacted[key_text] = _redact_mapping(item)
        return redacted
    if isinstance(value, (list, tuple)):
        return [_redact_mapping(item) for item in value]
    if isinstance(value, datetime):
        return _normalize_datetime(value)
    if isinstance(value, str) and ("sess_" in value or "access_pass" in value.lower() or "k1" in value.lower()):
        return redact_sensitive_auth_material(value)
    return value
