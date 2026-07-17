"""Validation for the Wallet + LNURL compatibility registry.

The registry is deployment metadata about wallet products. Validation fails closed
for unsafe capability claims, malformed enums, duplicate records, or embedded
secret/user material. It does not make authorization decisions.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from app.domain.wallet_auth.proofs import WalletVerificationStrength
from app.domain.wallet_auth.risks import WalletRiskLevel
from app.services.wallet_auth.wallet_compatibility import (
    CapabilityState,
    CustodyModel,
    DisplayAssurance,
    EvidenceConfidence,
    EvidenceType,
    QuirkSeverity,
    RegistryRecordStatus,
    WalletType,
)

SUPPORTED_SCHEMA_VERSION = 1
_FORBIDDEN_KEY_PARTS = (
    "seed",
    "mnemonic",
    "private_key",
    "privkey",
    "xprv",
    "wallet_address",
    "bitcoin_address",
    "linking_key",
    "k1",
    "raw_signature",
    "invoice",
    "payer_email",
    "raw_email",
)
_FORBIDDEN_VALUE_PARTS = ("xprv", "seed phrase", "mnemonic", "private key")


class CompatibilityConfigError(ValueError):
    """Raised when wallet compatibility configuration is unsafe or invalid."""


def validate_registry_config(raw: Mapping[str, Any]) -> None:
    """Validate raw YAML configuration before constructing registry records."""

    _reject_secret_material(raw)
    schema_version = raw.get("schema_version")
    if schema_version != SUPPORTED_SCHEMA_VERSION:
        raise CompatibilityConfigError("unsupported compatibility registry schema_version")
    defaults = _require_mapping(raw.get("defaults"), "defaults")
    unknown = _require_mapping(defaults.get("unknown_wallet"), "defaults.unknown_wallet")
    _validate_default_unknown(unknown)
    wallets = raw.get("wallets")
    if not isinstance(wallets, list):
        raise CompatibilityConfigError("wallets must be a list")
    seen: set[str] = set()
    for index, item in enumerate(wallets):
        record = _require_mapping(item, f"wallets[{index}]")
        slug = str(record.get("wallet_slug", "")).strip().lower()
        if not slug:
            raise CompatibilityConfigError("wallet_slug is required")
        if slug in seen:
            raise CompatibilityConfigError(f"duplicate wallet_slug: {slug}")
        seen.add(slug)
        _validate_record(record, f"wallets[{index}]")


def _validate_default_unknown(record: Mapping[str, Any]) -> None:
    status = _enum(RegistryRecordStatus, record.get("status", "unknown"), "unknown status")
    if status is not RegistryRecordStatus.UNKNOWN:
        raise CompatibilityConfigError("unknown wallet fallback must use status=unknown")
    security = _require_mapping(record.get("security"), "defaults.unknown_wallet.security")
    strength = _enum(
        WalletVerificationStrength,
        security.get("maximum_verification_strength", "compatibility"),
        "unknown wallet maximum_verification_strength",
    )
    if strength is WalletVerificationStrength.SOVEREIGN:
        raise CompatibilityConfigError("unknown wallet fallback cannot declare sovereign strength")


def _validate_record(record: Mapping[str, Any], path: str) -> None:
    for value in _require_sequence(record.get("wallet_type"), f"{path}.wallet_type"):
        _enum(WalletType, value, f"{path}.wallet_type")
    _enum(CustodyModel, record.get("custody_model", "unknown"), f"{path}.custody_model")
    status = _enum(RegistryRecordStatus, record.get("status", "unknown"), f"{path}.status")
    security = _require_mapping(record.get("security"), f"{path}.security")
    max_risk = _enum(WalletRiskLevel, security.get("maximum_risk_level", "low"), f"{path}.maximum_risk_level")
    strength = _enum(
        WalletVerificationStrength,
        security.get("maximum_verification_strength", "compatibility"),
        f"{path}.maximum_verification_strength",
    )
    if status is RegistryRecordStatus.BLOCKED and any(
        bool(security.get(name, False))
        for name in (
            "eligible_for_routine_login",
            "eligible_for_new_device_binding",
            "eligible_for_step_up",
            "eligible_for_recovery_factor",
            "eligible_for_business_quorum",
            "eligible_for_sovereign_quorum",
        )
    ):
        raise CompatibilityConfigError("blocked wallet cannot declare eligibility")
    if status is RegistryRecordStatus.UNKNOWN and strength is WalletVerificationStrength.SOVEREIGN:
        raise CompatibilityConfigError("unknown wallet cannot declare sovereign strength")
    bitcoin = _require_mapping(record.get("bitcoin_capabilities"), f"{path}.bitcoin_capabilities")
    _validate_bitcoin_capabilities(bitcoin, max_risk, path)
    lnurl = _require_mapping(record.get("lnurl_capabilities"), f"{path}.lnurl_capabilities")
    _validate_lnurl_capabilities(lnurl, path)
    for evidence in record.get("evidence", []) or []:
        ev = _require_mapping(evidence, f"{path}.evidence")
        _enum(EvidenceType, ev.get("evidence_type", "unknown"), f"{path}.evidence_type")
        _enum(EvidenceConfidence, ev.get("confidence", "unknown"), f"{path}.confidence")
    for quirk in record.get("known_quirks", []) or []:
        q = _require_mapping(quirk, f"{path}.known_quirks")
        _enum(QuirkSeverity, q.get("severity", "low"), f"{path}.quirk.severity")


def _validate_bitcoin_capabilities(
    bitcoin: Mapping[str, Any], max_risk: WalletRiskLevel, path: str
) -> None:
    for name in ("bip322", "legacy_message_signature", "psbt_support"):
        if name in bitcoin:
            cap = _require_mapping(bitcoin[name], f"{path}.bitcoin_capabilities.{name}")
            _enum(CapabilityState, cap.get("state", "unknown"), f"{path}.{name}.state")
    legacy = _require_mapping(
        bitcoin.get("legacy_message_signature", {}), f"{path}.bitcoin_capabilities.legacy_message_signature"
    )
    legacy_state = _enum(CapabilityState, legacy.get("state", "unknown"), f"{path}.legacy.state")
    if legacy_state not in {CapabilityState.UNSUPPORTED, CapabilityState.UNKNOWN}:
        risk = _enum(WalletRiskLevel, legacy.get("max_allowed_risk", "low"), f"{path}.legacy.max_allowed_risk")
        if risk is not WalletRiskLevel.LOW or max_risk not in {WalletRiskLevel.LOW, WalletRiskLevel.MEDIUM}:
            raise CompatibilityConfigError("legacy message signatures must remain low-risk only")


def _validate_lnurl_capabilities(lnurl: Mapping[str, Any], path: str) -> None:
    for section in ("auth", "pay", "withdraw", "verify"):
        data = _require_mapping(lnurl.get(section, {}), f"{path}.lnurl_capabilities.{section}")
        for key, value in data.items():
            if key == "payer_data_email_required" and value is True:
                raise CompatibilityConfigError("payerData.email must not be required by Bastion defaults")
            if key.endswith("display") or key.endswith("assurance"):
                _enum(DisplayAssurance, value, f"{path}.{section}.{key}")
            elif isinstance(value, str):
                _enum(CapabilityState, value, f"{path}.{section}.{key}")


def _reject_secret_material(value: Any, path: str = "registry") -> None:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            key_text = str(key).lower()
            if any(part in key_text for part in _FORBIDDEN_KEY_PARTS):
                raise CompatibilityConfigError(f"forbidden secret/user-specific field in registry: {path}.{key}")
            _reject_secret_material(nested, f"{path}.{key}")
    elif isinstance(value, Sequence) and not isinstance(value, str | bytes | bytearray):
        for index, item in enumerate(value):
            _reject_secret_material(item, f"{path}[{index}]")
    elif isinstance(value, str):
        lowered = value.lower()
        if any(part in lowered for part in _FORBIDDEN_VALUE_PARTS):
            raise CompatibilityConfigError(f"forbidden secret-like value in registry: {path}")


def _require_mapping(value: Any, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise CompatibilityConfigError(f"{name} must be a mapping")
    return value


def _require_sequence(value: Any, name: str) -> Sequence[Any]:
    if not isinstance(value, Sequence) or isinstance(value, str | bytes | bytearray):
        raise CompatibilityConfigError(f"{name} must be a sequence")
    return value


def _enum(enum_type: type[Any], value: Any, name: str) -> Any:
    try:
        return enum_type(value)
    except ValueError as exc:
        raise CompatibilityConfigError(f"invalid {name}: {value}") from exc
