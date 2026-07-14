"""Safe YAML loader for the Wallet + LNURL compatibility registry."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

from app.domain.wallet_auth.proofs import WalletScriptType, WalletVerificationStrength
from app.domain.wallet_auth.risks import WalletRiskLevel
from app.services.wallet_auth.compatibility_validation import (
    CompatibilityConfigError,
    validate_registry_config,
)
from app.services.wallet_auth.wallet_compatibility import (
    BitcoinProofCapabilities,
    Capability,
    CapabilityState,
    CompatibilityEvidence,
    CustodyModel,
    DisplayAssurance,
    EvidenceConfidence,
    EvidenceType,
    KnownQuirk,
    LNURLCapabilities,
    QuirkSeverity,
    RegistryRecordStatus,
    SecurityCompatibility,
    VersionConstraint,
    WalletCompatibilityRecord,
    WalletCompatibilityRegistry,
    WalletType,
)

DEFAULT_COMPATIBILITY_PATH = Path("config/wallet_auth_compatibility.yaml")


def load_wallet_compatibility_registry(
    path: str | Path = DEFAULT_COMPATIBILITY_PATH,
) -> WalletCompatibilityRegistry:
    """Load, validate, and freeze a compatibility registry from YAML."""

    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError as exc:
        raise CompatibilityConfigError("unable to read wallet compatibility registry") from exc
    return load_wallet_compatibility_yaml_text(text)


@lru_cache(maxsize=1)
def get_default_wallet_compatibility_registry() -> WalletCompatibilityRegistry:
    """Return the cached default registry snapshot."""

    return load_wallet_compatibility_registry(DEFAULT_COMPATIBILITY_PATH)


def reload_default_wallet_compatibility_registry() -> WalletCompatibilityRegistry:
    """Explicitly clear and reload the default registry snapshot."""

    get_default_wallet_compatibility_registry.cache_clear()
    return get_default_wallet_compatibility_registry()


def load_wallet_compatibility_yaml_text(text: str) -> WalletCompatibilityRegistry:
    """Load a registry from YAML text using safe construction only."""

    try:
        raw = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise CompatibilityConfigError("invalid wallet compatibility YAML") from exc
    if not isinstance(raw, Mapping):
        raise CompatibilityConfigError("wallet compatibility YAML must be a mapping")
    validate_registry_config(raw)
    return _registry_from_raw(raw)


def _registry_from_raw(raw: Mapping[str, Any]) -> WalletCompatibilityRegistry:
    defaults = raw["defaults"]
    if not isinstance(defaults, Mapping):
        raise CompatibilityConfigError("defaults must be a mapping")
    unknown_raw = defaults["unknown_wallet"]
    if not isinstance(unknown_raw, Mapping):
        raise CompatibilityConfigError("unknown_wallet must be a mapping")
    schema_version = int(raw["schema_version"])
    unknown = _record_from_raw(unknown_raw, schema_version=schema_version, fallback=True)
    wallets_raw = raw["wallets"]
    if not isinstance(wallets_raw, list):
        raise CompatibilityConfigError("wallets must be a list")
    records = {
        str(item["wallet_slug"]).strip().lower(): _record_from_raw(item, schema_version=schema_version)
        for item in wallets_raw
        if isinstance(item, Mapping)
    }
    return WalletCompatibilityRegistry(
        records=records,
        unknown_fallback=unknown,
        schema_version=schema_version,
        loaded_at=datetime.now(UTC),
    )


def _record_from_raw(
    raw: Mapping[str, Any], *, schema_version: int, fallback: bool = False
) -> WalletCompatibilityRecord:
    bitcoin = raw.get("bitcoin_capabilities", {})
    lnurl = raw.get("lnurl_capabilities", {})
    lightning = raw.get("lightning_capabilities", {})
    return WalletCompatibilityRecord(
        registry_id=str(raw.get("registry_id") or raw.get("wallet_slug") or "unknown-wallet"),
        wallet_slug=str(raw.get("wallet_slug", "unknown-wallet")).strip().lower(),
        display_name=str(raw.get("display_name", "Unknown Wallet")),
        vendor=str(raw.get("vendor", "Unknown")),
        wallet_type=tuple(WalletType(item) for item in raw.get("wallet_type", ["unknown"])),
        custody_model=CustodyModel(raw.get("custody_model", "unknown")),
        platforms=tuple(str(item) for item in raw.get("platforms", ["unknown"])),
        versions=_version_constraint(raw.get("versions", {})),
        bitcoin_capabilities=_bitcoin_capabilities(bitcoin if isinstance(bitcoin, Mapping) else {}),
        lnurl_capabilities=_lnurl_capabilities(
            lnurl if isinstance(lnurl, Mapping) else {},
            lightning if isinstance(lightning, Mapping) else {},
        ),
        security=_security(raw.get("security", {})),
        known_quirks=tuple(_quirk(item) for item in raw.get("known_quirks", []) or []),
        evidence=tuple(_evidence(item) for item in raw.get("evidence", []) or []),
        status=RegistryRecordStatus(raw.get("status", "unknown")),
        schema_version=schema_version,
        last_reviewed_at=None if fallback else raw.get("last_reviewed_at"),
        reviewed_by=None if fallback else raw.get("reviewed_by"),
        source_references=tuple(str(item) for item in raw.get("source_references", []) or []),
    )


def _version_constraint(raw: Any) -> VersionConstraint:
    if not isinstance(raw, Mapping):
        return VersionConstraint()
    return VersionConstraint(
        minimum_supported=raw.get("minimum_supported"),
        maximum_supported=raw.get("maximum_supported"),
    )


def _bitcoin_capabilities(raw: Mapping[str, Any]) -> BitcoinProofCapabilities:
    return BitcoinProofCapabilities(
        bip322=_capability(raw.get("bip322", {})),
        legacy_message_signature=_capability(raw.get("legacy_message_signature", {})),
        psbt_support_metadata_only=CapabilityState(
            _mapping(raw.get("psbt_support", {})).get("state", "unknown")
        ),
    )


def _lnurl_capabilities(
    raw: Mapping[str, Any], lightning_raw: Mapping[str, Any] | None = None
) -> LNURLCapabilities:
    lightning_data = lightning_raw or {}
    return LNURLCapabilities(
        auth=_state_mapping(_mapping(raw.get("auth", {}))),
        pay=_state_mapping(_mapping(raw.get("pay", {}))),
        lightning_address=_state_mapping(
            _mapping(raw.get("lightning_address", lightning_data.get("lightning_address", {})))
        ),
        withdraw=_state_mapping(_mapping(raw.get("withdraw", {}))),
        verify=_state_mapping(_mapping(raw.get("verify", {}))),
        display_assurance=DisplayAssurance(
            _mapping(raw.get("auth", {})).get("domain_display", "unknown")
        ),
    )


def _capability(raw: Any) -> Capability:
    data = _mapping(raw)
    return Capability(
        state=CapabilityState(data.get("state", "unknown")),
        supported_script_types=tuple(
            WalletScriptType(item) for item in data.get("supported_script_types", [])
        ),
        supported_networks=tuple(str(item) for item in data.get("supported_networks", [])),
        max_allowed_risk=WalletRiskLevel(data.get("max_allowed_risk", "low")),
        display_assurance=DisplayAssurance(data.get("structured_message_display", "unknown")),
        metadata={str(k): v for k, v in data.items() if k not in {"supported_script_types"}},
    )


def _state_mapping(raw: Mapping[str, Any]) -> Mapping[str, CapabilityState]:
    return {
        str(key): CapabilityState(value)
        for key, value in raw.items()
        if isinstance(value, str) and value in {state.value for state in CapabilityState}
    }


def _security(raw: Any) -> SecurityCompatibility:
    data = _mapping(raw)
    return SecurityCompatibility(
        maximum_risk_level=WalletRiskLevel(data.get("maximum_risk_level", "low")),
        maximum_verification_strength=WalletVerificationStrength(
            data.get("maximum_verification_strength", "compatibility")
        ),
        eligible_for_routine_login=bool(data.get("eligible_for_routine_login", False)),
        eligible_for_new_device_binding=bool(data.get("eligible_for_new_device_binding", False)),
        eligible_for_step_up=bool(data.get("eligible_for_step_up", False)),
        eligible_for_recovery_factor=bool(data.get("eligible_for_recovery_factor", False)),
        eligible_for_business_quorum=bool(data.get("eligible_for_business_quorum", False)),
        eligible_for_sovereign_quorum=bool(data.get("eligible_for_sovereign_quorum", False)),
        requires_access_certificate=bool(data.get("requires_access_certificate", False)),
        requires_additional_bip322_proof=bool(data.get("requires_additional_bip322_proof", True)),
        requires_hardware_confirmation=bool(data.get("requires_hardware_confirmation", False)),
        requires_manual_review=bool(data.get("requires_manual_review", False)),
    )


def _evidence(raw: Any) -> CompatibilityEvidence:
    data = _mapping(raw)
    return CompatibilityEvidence(
        evidence_type=EvidenceType(data.get("evidence_type", "unknown")),
        source=str(data.get("source", "unknown")),
        tested_version=data.get("tested_version"),
        tested_at=data.get("tested_at"),
        test_network=data.get("test_network"),
        reviewer=data.get("reviewer"),
        notes=data.get("notes"),
        confidence=EvidenceConfidence(data.get("confidence", "unknown")),
    )


def _quirk(raw: Any) -> KnownQuirk:
    data = _mapping(raw)
    return KnownQuirk(
        quirk_id=str(data.get("quirk_id", "unknown-quirk")),
        severity=QuirkSeverity(data.get("severity", "low")),
        capability=str(data.get("capability", "unknown")),
        affected_versions=data.get("affected_versions"),
        description=str(data.get("description", "")),
        mitigation=str(data.get("mitigation", "manual_review_required")),
        security_effect=str(data.get("security_effect", "unknown")),
        resolved_in_version=data.get("resolved_in_version"),
        active=bool(data.get("active", True)),
    )


def _mapping(raw: Any) -> Mapping[str, Any]:
    return raw if isinstance(raw, Mapping) else {}
