"""Wallet + LNURL compatibility registry.

The registry describes product capabilities and limitations. It does not verify
wallet proofs, settle payments, create sessions, or authorize access. Unknown
wallets are conservative, and wallet names/client claims never bypass runtime
cryptographic verification or Policy Engine decisions.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any

from app.domain.wallet_auth.proofs import WalletProofType, WalletScriptType, WalletVerificationStrength
from app.domain.wallet_auth.risks import WalletRiskLevel
from app.services.access.crypto.hashing import canonical_json, sha256_prefixed


class CapabilityState(StrEnum):
    SUPPORTED = "supported"
    UNSUPPORTED = "unsupported"
    PARTIAL = "partial"
    VERSION_DEPENDENT = "version_dependent"
    UNVERIFIED = "unverified"
    DEPRECATED = "deprecated"
    UNKNOWN = "unknown"


class WalletType(StrEnum):
    MOBILE = "mobile"
    DESKTOP = "desktop"
    BROWSER = "browser"
    BROWSER_EXTENSION = "browser_extension"
    HARDWARE = "hardware"
    COMMAND_LINE = "command_line"
    SERVER = "server"
    EMBEDDED = "embedded"
    PAYREGISTER_TERMINAL = "payregister_terminal"
    CUSTODIAL_SERVICE = "custodial_service"
    UNKNOWN = "unknown"


class CustodyModel(StrEnum):
    NON_CUSTODIAL = "non_custodial"
    CUSTODIAL = "custodial"
    HYBRID = "hybrid"
    WATCH_ONLY = "watch_only"
    UNKNOWN = "unknown"


class RegistryRecordStatus(StrEnum):
    ACTIVE = "active"
    EXPERIMENTAL = "experimental"
    DEPRECATED = "deprecated"
    BLOCKED = "blocked"
    UNKNOWN = "unknown"


class DisplayAssurance(StrEnum):
    CLEAR = "clear"
    PARTIAL = "partial"
    OPAQUE = "opaque"
    UNKNOWN = "unknown"


class EvidenceType(StrEnum):
    OFFICIAL_DOCUMENTATION = "official_documentation"
    REPRODUCIBLE_TEST = "reproducible_test"
    INTEGRATION_TEST = "integration_test"
    VENDOR_STATEMENT = "vendor_statement"
    COMMUNITY_REPORT = "community_report"
    MANUAL_REVIEW = "manual_review"
    UNKNOWN = "unknown"


class EvidenceConfidence(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


class QuirkSeverity(StrEnum):
    INFORMATIONAL = "informational"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True, slots=True)
class VersionConstraint:
    minimum_supported: str | None = None
    maximum_supported: str | None = None

    def matches(self, version: str | None) -> bool | None:
        if version is None or version == "":
            return None
        parsed = _parse_version(version)
        if parsed is None:
            return False
        if self.minimum_supported and parsed < (_parse_version(self.minimum_supported) or (999999,)):
            return False
        if self.maximum_supported and parsed > (_parse_version(self.maximum_supported) or (-1,)):
            return False
        return True


@dataclass(frozen=True, slots=True)
class Capability:
    state: CapabilityState = CapabilityState.UNKNOWN
    supported_script_types: tuple[WalletScriptType, ...] = ()
    supported_networks: tuple[str, ...] = ()
    max_allowed_risk: WalletRiskLevel = WalletRiskLevel.LOW
    display_assurance: DisplayAssurance = DisplayAssurance.UNKNOWN
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class BitcoinProofCapabilities:
    bip322: Capability = Capability()
    legacy_message_signature: Capability = Capability()
    p2wpkh: CapabilityState = CapabilityState.UNKNOWN
    p2tr: CapabilityState = CapabilityState.UNKNOWN
    p2sh: CapabilityState = CapabilityState.UNKNOWN
    p2wsh: CapabilityState = CapabilityState.UNKNOWN
    p2pkh: CapabilityState = CapabilityState.UNKNOWN
    hardware_display_confirmation: CapabilityState = CapabilityState.UNKNOWN
    message_domain_display: DisplayAssurance = DisplayAssurance.UNKNOWN
    structured_intent_display: DisplayAssurance = DisplayAssurance.UNKNOWN
    air_gapped_signing: CapabilityState = CapabilityState.UNKNOWN
    qr_signature_transport: CapabilityState = CapabilityState.UNKNOWN
    psbt_support_metadata_only: CapabilityState = CapabilityState.UNKNOWN
    descriptor_export_metadata_only: CapabilityState = CapabilityState.UNKNOWN


@dataclass(frozen=True, slots=True)
class LNURLCapabilities:
    auth: Mapping[str, CapabilityState] = field(default_factory=dict)
    pay: Mapping[str, CapabilityState] = field(default_factory=dict)
    lightning_address: Mapping[str, CapabilityState] = field(default_factory=dict)
    withdraw: Mapping[str, CapabilityState] = field(default_factory=dict)
    verify: Mapping[str, CapabilityState] = field(default_factory=dict)
    display_assurance: DisplayAssurance = DisplayAssurance.UNKNOWN


@dataclass(frozen=True, slots=True)
class SecurityCompatibility:
    maximum_risk_level: WalletRiskLevel = WalletRiskLevel.LOW
    maximum_verification_strength: WalletVerificationStrength = WalletVerificationStrength.COMPATIBILITY
    eligible_for_routine_login: bool = False
    eligible_for_new_device_binding: bool = False
    eligible_for_step_up: bool = False
    eligible_for_recovery_factor: bool = False
    eligible_for_business_quorum: bool = False
    eligible_for_sovereign_quorum: bool = False
    requires_access_certificate: bool = False
    requires_additional_bip322_proof: bool = True
    requires_hardware_confirmation: bool = False
    requires_manual_review: bool = False


@dataclass(frozen=True, slots=True)
class CompatibilityEvidence:
    evidence_type: EvidenceType
    source: str
    tested_version: str | None
    tested_at: str | None
    test_network: str | None
    reviewer: str | None
    notes: str | None
    confidence: EvidenceConfidence


@dataclass(frozen=True, slots=True)
class KnownQuirk:
    quirk_id: str
    severity: QuirkSeverity
    capability: str
    affected_versions: str | None
    description: str
    mitigation: str
    security_effect: str
    resolved_in_version: str | None
    active: bool

    def applies_to(self, version: str | None) -> bool:
        if not self.active:
            return False
        if self.resolved_in_version and version and (_parse_version(version) or (0,)) >= (_parse_version(self.resolved_in_version) or (999999,)):
            return False
        return True


@dataclass(frozen=True, slots=True)
class WalletCompatibilityRecord:
    registry_id: str
    wallet_slug: str
    display_name: str
    vendor: str
    wallet_type: tuple[WalletType, ...]
    custody_model: CustodyModel
    platforms: tuple[str, ...]
    versions: VersionConstraint
    bitcoin_capabilities: BitcoinProofCapabilities
    lnurl_capabilities: LNURLCapabilities
    security: SecurityCompatibility
    known_quirks: tuple[KnownQuirk, ...]
    evidence: tuple[CompatibilityEvidence, ...]
    status: RegistryRecordStatus
    schema_version: int
    last_reviewed_at: str | None = None
    reviewed_by: str | None = None
    source_references: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class CompatibilityQuery:
    wallet_slug: str
    capability: str
    wallet_version: str | None = None
    proof_type: WalletProofType | None = None
    script_type: WalletScriptType | None = None
    network: str | None = None
    action: str | None = None
    requested_risk_level: WalletRiskLevel = WalletRiskLevel.LOW
    client_claims: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class CompatibilityResult:
    compatible: bool
    state: CapabilityState
    wallet_slug: str
    wallet_version: str | None
    capability: str
    maximum_risk_level: WalletRiskLevel
    maximum_verification_strength: WalletVerificationStrength
    limitations: tuple[str, ...]
    active_quirks: tuple[KnownQuirk, ...]
    evidence_confidence: EvidenceConfidence
    requires_additional_proof: bool
    reason_code: str


@dataclass(frozen=True, slots=True)
class RegistryMetadata:
    schema_version: int
    registry_hash: str
    loaded_at: datetime
    record_count: int


class WalletCompatibilityRegistry:
    def __init__(self, *, records: Mapping[str, WalletCompatibilityRecord], unknown_fallback: WalletCompatibilityRecord, schema_version: int, loaded_at: datetime) -> None:
        self.records = dict(records)
        self.unknown_fallback = unknown_fallback
        self.schema_version = schema_version
        self.loaded_at = loaded_at
        self._hash = registry_snapshot_hash(schema_version=schema_version, records=self.records, unknown_fallback=unknown_fallback)

    def registry_snapshot_hash(self) -> str:
        return self._hash

    def metadata(self) -> RegistryMetadata:
        return RegistryMetadata(self.schema_version, self._hash, self.loaded_at, len(self.records))

    def get_unknown_wallet_fallback(self) -> WalletCompatibilityRecord:
        return self.unknown_fallback

    def get_wallet(self, wallet_slug: str, wallet_version: str | None = None) -> WalletCompatibilityRecord | None:
        record = self.records.get(_slug(wallet_slug))
        if record is None:
            return None
        match = record.versions.matches(wallet_version)
        if match is False:
            return None
        return record

    def resolve_wallet(self, wallet_slug: str, wallet_version: str | None = None) -> WalletCompatibilityRecord:
        return self.get_wallet(wallet_slug, wallet_version) or self.unknown_fallback

    def supports_bitcoin_proof(self, wallet_slug: str, proof_type: WalletProofType, script_type: WalletScriptType | None = None, network: str | None = None, wallet_version: str | None = None) -> CompatibilityResult:
        record = self.resolve_wallet(wallet_slug, wallet_version)
        if proof_type is WalletProofType.BIP322:
            capability = record.bitcoin_capabilities.bip322
            cap_name = "bip322"
        elif proof_type is WalletProofType.LEGACY_MESSAGE_SIGNATURE:
            capability = record.bitcoin_capabilities.legacy_message_signature
            cap_name = "legacy_message_signature"
        else:
            return self._result(record, wallet_version, str(proof_type.value), CapabilityState.UNSUPPORTED, "capability_unsupported")
        if script_type and capability.supported_script_types and script_type not in capability.supported_script_types:
            return self._result(record, wallet_version, cap_name, CapabilityState.UNSUPPORTED, "capability_unsupported", ("script_type_not_supported",))
        if network and capability.supported_networks and network not in capability.supported_networks:
            return self._result(record, wallet_version, cap_name, CapabilityState.UNKNOWN, "capability_unknown", ("network_not_declared",))
        reason = "legacy_proof_low_risk_only" if proof_type is WalletProofType.LEGACY_MESSAGE_SIGNATURE else _reason_for_state(capability.state)
        return self._result(record, wallet_version, cap_name, capability.state, reason)

    def supports_lnurl_auth(self, wallet_slug: str, action: str | None = None, wallet_version: str | None = None) -> CompatibilityResult:
        record = self.resolve_wallet(wallet_slug, wallet_version)
        state = record.lnurl_capabilities.auth.get(action or "state", record.lnurl_capabilities.auth.get("state", CapabilityState.UNKNOWN))
        reason = "action_display_insufficient" if action == "auth" and record.lnurl_capabilities.display_assurance in {DisplayAssurance.OPAQUE, DisplayAssurance.UNKNOWN} else _reason_for_state(state)
        return self._result(record, wallet_version, f"lnurl_auth:{action or 'state'}", state, reason)

    def supports_lnurl_pay(self, wallet_slug: str, wallet_version: str | None = None) -> CompatibilityResult:
        return self._lnurl_result(wallet_slug, wallet_version, "pay", "state")

    def supports_lightning_address(self, wallet_slug: str, wallet_version: str | None = None) -> CompatibilityResult:
        return self._lnurl_result(wallet_slug, wallet_version, "lightning_address", "state")

    def supports_lnurl_withdraw(self, wallet_slug: str, wallet_version: str | None = None) -> CompatibilityResult:
        return self._lnurl_result(wallet_slug, wallet_version, "withdraw", "state", reason_override="capability_supported_not_authorization")

    def supports_lnurl_verify(self, wallet_slug: str, wallet_version: str | None = None) -> CompatibilityResult:
        return self._lnurl_result(wallet_slug, wallet_version, "verify", "state")

    def supports_payerdata_auth(self, wallet_slug: str, wallet_version: str | None = None) -> CompatibilityResult:
        return self._lnurl_result(wallet_slug, wallet_version, "pay", "payer_data_auth")

    def supports_success_action(self, wallet_slug: str, action_type: str, wallet_version: str | None = None) -> CompatibilityResult:
        key = f"success_action_{action_type}"
        return self._lnurl_result(wallet_slug, wallet_version, "pay", key)

    def get_known_quirks(self, wallet_slug: str, wallet_version: str | None = None) -> tuple[KnownQuirk, ...]:
        record = self.resolve_wallet(wallet_slug, wallet_version)
        return tuple(quirk for quirk in record.known_quirks if quirk.applies_to(wallet_version))

    def get_maximum_risk_level(self, wallet_slug: str, wallet_version: str | None = None) -> WalletRiskLevel:
        return self.resolve_wallet(wallet_slug, wallet_version).security.maximum_risk_level

    def get_maximum_verification_strength(self, wallet_slug: str, wallet_version: str | None = None) -> WalletVerificationStrength:
        return self.resolve_wallet(wallet_slug, wallet_version).security.maximum_verification_strength

    def evaluate_action_compatibility(self, query: CompatibilityQuery) -> CompatibilityResult:
        record = self.resolve_wallet(query.wallet_slug, query.wallet_version)
        if record.status is RegistryRecordStatus.BLOCKED:
            return self._result(record, query.wallet_version, query.capability, CapabilityState.UNSUPPORTED, "wallet_blocked")
        if query.requested_risk_level in {WalletRiskLevel.HIGH, WalletRiskLevel.CRITICAL} and record.security.maximum_risk_level is WalletRiskLevel.LOW:
            return self._result(record, query.wallet_version, query.capability, CapabilityState.UNSUPPORTED, "additional_bip322_required", ("requested_risk_exceeds_registry_maximum",))
        if query.proof_type:
            return self.supports_bitcoin_proof(query.wallet_slug, query.proof_type, query.script_type, query.network, query.wallet_version)
        return self._result(record, query.wallet_version, query.capability, CapabilityState.UNKNOWN, "capability_unknown")

    def _lnurl_result(self, wallet_slug: str, wallet_version: str | None, section: str, key: str, reason_override: str | None = None) -> CompatibilityResult:
        record = self.resolve_wallet(wallet_slug, wallet_version)
        data = getattr(record.lnurl_capabilities, section)
        state = data.get(key, CapabilityState.UNKNOWN)
        return self._result(record, wallet_version, f"lnurl_{section}:{key}", state, reason_override or _reason_for_state(state))

    def _result(self, record: WalletCompatibilityRecord, version: str | None, capability: str, state: CapabilityState, reason: str, extra_limitations: Sequence[str] = ()) -> CompatibilityResult:
        quirks = tuple(quirk for quirk in record.known_quirks if quirk.applies_to(version))
        limitations = list(extra_limitations)
        if record.wallet_slug == self.unknown_fallback.wallet_slug or record.status is RegistryRecordStatus.UNKNOWN:
            limitations.append("unknown_wallet_conservative_fallback")
            reason = "wallet_unknown" if reason == "capability_unknown" else reason
        if record.status is RegistryRecordStatus.BLOCKED:
            limitations.append("blocked_wallet_record")
            reason = "wallet_blocked"
            state = CapabilityState.UNSUPPORTED
        if capability.startswith("lnurl_auth"):
            limitations.append("lnurl_auth_not_onchain_ownership")
        if capability.startswith("lnurl_pay"):
            limitations.append("lnurl_pay_not_settlement_proof")
        if capability.startswith("lnurl_lightning_address"):
            limitations.append("lightning_address_not_identity")
        if capability.startswith("lnurl_withdraw"):
            limitations.append("lnurl_withdraw_not_payout_authorization")
        for quirk in quirks:
            if quirk.severity is QuirkSeverity.CRITICAL and quirk.capability in {capability, capability.split(":", 1)[0]}:
                limitations.append("critical_quirk_active")
                reason = "critical_quirk_active"
                state = CapabilityState.UNSUPPORTED
            elif quirk.severity is QuirkSeverity.HIGH:
                limitations.append("high_quirk_lowers_assurance")
        confidence = _evidence_confidence(record.evidence)
        return CompatibilityResult(
            compatible=state in {CapabilityState.SUPPORTED, CapabilityState.PARTIAL},
            state=state,
            wallet_slug=record.wallet_slug,
            wallet_version=_safe_version(version),
            capability=capability,
            maximum_risk_level=record.security.maximum_risk_level,
            maximum_verification_strength=record.security.maximum_verification_strength,
            limitations=tuple(dict.fromkeys((*limitations, "registry_is_not_authorization", "runtime_proof_verification_required"))),
            active_quirks=quirks,
            evidence_confidence=confidence,
            requires_additional_proof=record.security.requires_additional_bip322_proof or state is not CapabilityState.SUPPORTED,
            reason_code=reason,
        )


def registry_snapshot_hash(*, schema_version: int, records: Mapping[str, WalletCompatibilityRecord], unknown_fallback: WalletCompatibilityRecord) -> str:
    normalized = {
        "schema_version": schema_version,
        "unknown_fallback": _record_to_json(unknown_fallback),
        "records": {key: _record_to_json(value) for key, value in sorted(records.items())},
    }
    return sha256_prefixed(canonical_json(normalized))


def _record_to_json(record: WalletCompatibilityRecord) -> dict[str, Any]:
    return {
        "registry_id": record.registry_id,
        "wallet_slug": record.wallet_slug,
        "display_name": record.display_name,
        "vendor": record.vendor,
        "wallet_type": [item.value for item in record.wallet_type],
        "custody_model": record.custody_model.value,
        "platforms": list(record.platforms),
        "versions": {"minimum_supported": record.versions.minimum_supported, "maximum_supported": record.versions.maximum_supported},
        "security": _security_json(record.security),
        "bitcoin_capabilities": {
            "bip322": _cap_json(record.bitcoin_capabilities.bip322),
            "legacy_message_signature": _cap_json(record.bitcoin_capabilities.legacy_message_signature),
        },
        "lnurl_capabilities": {
            "auth": {k: v.value for k, v in sorted(record.lnurl_capabilities.auth.items())},
            "pay": {k: v.value for k, v in sorted(record.lnurl_capabilities.pay.items())},
            "lightning_address": {k: v.value for k, v in sorted(record.lnurl_capabilities.lightning_address.items())},
            "withdraw": {k: v.value for k, v in sorted(record.lnurl_capabilities.withdraw.items())},
            "verify": {k: v.value for k, v in sorted(record.lnurl_capabilities.verify.items())},
            "display_assurance": record.lnurl_capabilities.display_assurance.value,
        },
        "known_quirks": [_quirk_json(q) for q in sorted(record.known_quirks, key=lambda q: q.quirk_id)],
        "evidence": [_evidence_json(e) for e in record.evidence],
        "status": record.status.value,
        "source_references": list(record.source_references),
    }


def _security_json(security: SecurityCompatibility) -> dict[str, Any]:
    return {
        "maximum_risk_level": security.maximum_risk_level.value,
        "maximum_verification_strength": security.maximum_verification_strength.value,
        "eligible_for_routine_login": security.eligible_for_routine_login,
        "eligible_for_new_device_binding": security.eligible_for_new_device_binding,
        "eligible_for_step_up": security.eligible_for_step_up,
        "eligible_for_recovery_factor": security.eligible_for_recovery_factor,
        "eligible_for_business_quorum": security.eligible_for_business_quorum,
        "eligible_for_sovereign_quorum": security.eligible_for_sovereign_quorum,
        "requires_access_certificate": security.requires_access_certificate,
        "requires_additional_bip322_proof": security.requires_additional_bip322_proof,
        "requires_hardware_confirmation": security.requires_hardware_confirmation,
        "requires_manual_review": security.requires_manual_review,
    }


def _cap_json(capability: Capability) -> dict[str, Any]:
    return {
        "state": capability.state.value,
        "supported_script_types": [item.value for item in capability.supported_script_types],
        "supported_networks": list(capability.supported_networks),
        "max_allowed_risk": capability.max_allowed_risk.value,
        "display_assurance": capability.display_assurance.value,
        "metadata": dict(capability.metadata),
    }


def _quirk_json(quirk: KnownQuirk) -> dict[str, Any]:
    return {
        "quirk_id": quirk.quirk_id,
        "severity": quirk.severity.value,
        "capability": quirk.capability,
        "affected_versions": quirk.affected_versions,
        "description": quirk.description,
        "mitigation": quirk.mitigation,
        "security_effect": quirk.security_effect,
        "resolved_in_version": quirk.resolved_in_version,
        "active": quirk.active,
    }


def _evidence_json(evidence: CompatibilityEvidence) -> dict[str, Any]:
    return {
        "evidence_type": evidence.evidence_type.value,
        "source": evidence.source,
        "tested_version": evidence.tested_version,
        "tested_at": evidence.tested_at,
        "test_network": evidence.test_network,
        "reviewer": evidence.reviewer,
        "notes": evidence.notes,
        "confidence": evidence.confidence.value,
    }


def _evidence_confidence(evidence: tuple[CompatibilityEvidence, ...]) -> EvidenceConfidence:
    rank = {EvidenceConfidence.UNKNOWN: 0, EvidenceConfidence.LOW: 1, EvidenceConfidence.MEDIUM: 2, EvidenceConfidence.HIGH: 3}
    best = EvidenceConfidence.UNKNOWN
    for item in evidence:
        if rank[item.confidence] > rank[best]:
            best = item.confidence
    return best


def _reason_for_state(state: CapabilityState) -> str:
    return {
        CapabilityState.SUPPORTED: "capability_supported",
        CapabilityState.PARTIAL: "capability_partial",
        CapabilityState.UNKNOWN: "capability_unknown",
        CapabilityState.UNSUPPORTED: "capability_unsupported",
        CapabilityState.UNVERIFIED: "capability_unknown",
        CapabilityState.DEPRECATED: "wallet_deprecated",
        CapabilityState.VERSION_DEPENDENT: "version_unknown",
    }[state]


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9-]+", "-", value.strip().lower()).strip("-") or "unknown-wallet"


def _safe_version(version: str | None) -> str | None:
    if version is None:
        return None
    parsed = _parse_version(version)
    return ".".join(str(part) for part in parsed) if parsed else "malformed"


def _parse_version(value: str) -> tuple[int, ...] | None:
    text = value.strip().lstrip("v")
    if not re.fullmatch(r"\d+(?:\.\d+){0,3}", text):
        return None
    return tuple(int(part) for part in text.split("."))
