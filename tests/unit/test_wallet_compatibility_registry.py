from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest
import yaml

from app.domain.wallet_auth.proofs import WalletProofType, WalletScriptType, WalletVerificationStrength
from app.domain.wallet_auth.risks import WalletRiskLevel
from app.services.wallet_auth.compatibility_loader import load_wallet_compatibility_yaml_text
from app.services.wallet_auth.compatibility_validation import CompatibilityConfigError
from app.services.wallet_auth.wallet_compatibility import (
    CapabilityState,
    CompatibilityQuery,
    WalletCompatibilityRegistry,
)

CONFIG_PATH = Path("config/wallet_auth_compatibility.yaml")


def _base_raw() -> dict:
    return yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))


def _registry(raw: dict | None = None) -> WalletCompatibilityRegistry:
    return load_wallet_compatibility_yaml_text(yaml.safe_dump(raw or _base_raw(), sort_keys=False))


def _add_test_lnurl_wallet(raw: dict) -> None:
    raw["wallets"].append(
        {
            "registry_id": "test-lnurl-v1",
            "wallet_slug": "test-lnurl-wallet",
            "display_name": "Test LNURL Wallet",
            "vendor": "Test Fixtures",
            "wallet_type": ["mobile"],
            "custody_model": "unknown",
            "platforms": ["test"],
            "versions": {"minimum_supported": "2.0.0", "maximum_supported": None},
            "bitcoin_capabilities": {
                "bip322": {
                    "state": "supported",
                    "supported_script_types": ["p2wpkh", "p2tr"],
                    "supported_networks": ["bitcoin-mainnet"],
                },
                "legacy_message_signature": {"state": "unsupported", "max_allowed_risk": "low"},
                "psbt_support": {"state": "supported", "metadata_only": True},
            },
            "lightning_capabilities": {"lightning_address": {"state": "supported"}},
            "lnurl_capabilities": {
                "auth": {
                    "state": "supported",
                    "register": "supported",
                    "login": "supported",
                    "link": "supported",
                    "auth": "partial",
                    "domain_display": "opaque",
                },
                "pay": {
                    "state": "supported",
                    "comment_allowed": "supported",
                    "payer_data": "supported",
                    "payer_data_auth": "supported",
                    "success_action_message": "supported",
                    "success_action_url": "partial",
                    "verify_url": "unknown",
                },
                "withdraw": {"state": "partial"},
                "verify": {"state": "unknown"},
            },
            "security": {
                "maximum_risk_level": "medium",
                "maximum_verification_strength": "standard",
                "eligible_for_routine_login": True,
                "eligible_for_new_device_binding": False,
                "eligible_for_step_up": False,
                "eligible_for_recovery_factor": False,
                "eligible_for_business_quorum": False,
                "eligible_for_sovereign_quorum": False,
                "requires_access_certificate": False,
                "requires_additional_bip322_proof": False,
                "requires_hardware_confirmation": True,
                "requires_manual_review": False,
            },
            "status": "active",
            "evidence": [
                {
                    "evidence_type": "integration_test",
                    "source": "unit-test-fixture",
                    "tested_version": "2.1.0",
                    "tested_at": "2026-07-13T00:00:00+00:00",
                    "test_network": "bitcoin-mainnet",
                    "reviewer": "tests",
                    "notes": "Synthetic test fixture, not a real product claim.",
                    "confidence": "high",
                }
            ],
            "known_quirks": [
                {
                    "quirk_id": "opaque-domain-display",
                    "severity": "high",
                    "capability": "lnurl_auth",
                    "affected_versions": None,
                    "description": "Fixture wallet does not clearly display auth domain.",
                    "mitigation": "require_additional_bip322_proof",
                    "security_effect": "critical LNURL step-up denied",
                    "resolved_in_version": "2.2.0",
                    "active": True,
                }
            ],
            "source_references": ["unit-test-fixture"],
        }
    )


def test_valid_yaml_loads() -> None:
    registry = _registry()
    assert registry.metadata().schema_version == 1
    assert registry.metadata().record_count >= 2


def test_unsafe_yaml_construct_rejected() -> None:
    with pytest.raises(CompatibilityConfigError):
        load_wallet_compatibility_yaml_text("!!python/object/apply:os.system ['echo unsafe']")


def test_duplicate_wallet_slug_rejected() -> None:
    raw = _base_raw()
    raw["wallets"].append(deepcopy(raw["wallets"][0]))
    with pytest.raises(CompatibilityConfigError, match="duplicate wallet_slug"):
        _registry(raw)


def test_unsupported_schema_version_rejected() -> None:
    raw = _base_raw()
    raw["schema_version"] = 999
    with pytest.raises(CompatibilityConfigError, match="schema_version"):
        _registry(raw)


def test_malformed_enum_rejected() -> None:
    raw = _base_raw()
    raw["wallets"][0]["status"] = "super_trusted"
    with pytest.raises(CompatibilityConfigError, match="invalid"):
        _registry(raw)


def test_impossible_security_combination_rejected() -> None:
    raw = _base_raw()
    raw["wallets"][0]["status"] = "blocked"
    raw["wallets"][0]["security"]["eligible_for_routine_login"] = True
    with pytest.raises(CompatibilityConfigError, match="blocked wallet"):
        _registry(raw)


def test_forbidden_secret_fields_rejected() -> None:
    raw = _base_raw()
    raw["wallets"][0]["test_seed_phrase"] = "abandon abandon abandon"
    with pytest.raises(CompatibilityConfigError, match="forbidden"):
        _registry(raw)


def test_unknown_wallet_conservative_fallback() -> None:
    registry = _registry()
    result = registry.evaluate_action_compatibility(
        CompatibilityQuery(
            wallet_slug="not-a-real-wallet",
            capability="critical_step_up",
            requested_risk_level=WalletRiskLevel.CRITICAL,
        )
    )
    assert result.compatible is False
    assert result.reason_code in {"wallet_unknown", "additional_bip322_required"}
    assert result.maximum_verification_strength is WalletVerificationStrength.COMPATIBILITY
    assert "unknown_wallet_conservative_fallback" in result.limitations


def test_unknown_wallet_cannot_recovery_or_sovereign() -> None:
    registry = _registry()
    fallback = registry.get_unknown_wallet_fallback()
    assert fallback.security.eligible_for_recovery_factor is False
    assert fallback.security.eligible_for_sovereign_quorum is False


def test_bip322_capability_query_is_structured() -> None:
    raw = _base_raw()
    _add_test_lnurl_wallet(raw)
    result = _registry(raw).supports_bitcoin_proof(
        "test-lnurl-wallet",
        WalletProofType.BIP322,
        script_type=WalletScriptType.P2WPKH,
        network="bitcoin-mainnet",
        wallet_version="2.1.0",
    )
    assert result.compatible is True
    assert result.state is CapabilityState.SUPPORTED
    assert result.reason_code == "capability_supported"
    assert "registry_is_not_authorization" in result.limitations


def test_unsupported_script_type_fails_compatibly() -> None:
    raw = _base_raw()
    _add_test_lnurl_wallet(raw)
    result = _registry(raw).supports_bitcoin_proof(
        "test-lnurl-wallet", WalletProofType.BIP322, script_type=WalletScriptType.P2WSH
    )
    assert result.compatible is False
    assert result.reason_code == "capability_unsupported"


def test_wrong_network_capability_not_assumed() -> None:
    raw = _base_raw()
    _add_test_lnurl_wallet(raw)
    result = _registry(raw).supports_bitcoin_proof(
        "test-lnurl-wallet", WalletProofType.BIP322, network="bitcoin-signet"
    )
    assert result.compatible is False
    assert result.reason_code == "capability_unknown"


def test_legacy_only_wallet_is_low_risk_only() -> None:
    result = _registry().supports_bitcoin_proof(
        "generic-legacy-message-wallet", WalletProofType.LEGACY_MESSAGE_SIGNATURE
    )
    assert result.compatible is True
    assert result.maximum_risk_level is WalletRiskLevel.LOW
    assert result.maximum_verification_strength is WalletVerificationStrength.COMPATIBILITY
    assert result.reason_code == "legacy_proof_low_risk_only"


def test_psbt_capability_is_metadata_only_not_authorization() -> None:
    raw = _base_raw()
    _add_test_lnurl_wallet(raw)
    record = _registry(raw).resolve_wallet("test-lnurl-wallet")
    assert record.bitcoin_capabilities.psbt_support_metadata_only is CapabilityState.SUPPORTED
    assert not hasattr(record, "transaction_signing_authorized")


def test_lnurl_auth_action_support_queryable_and_opaque_display_reduces_step_up() -> None:
    raw = _base_raw()
    _add_test_lnurl_wallet(raw)
    registry = _registry(raw)
    login = registry.supports_lnurl_auth("test-lnurl-wallet", action="login")
    auth = registry.supports_lnurl_auth("test-lnurl-wallet", action="auth")
    assert login.compatible is True
    assert auth.reason_code == "action_display_insufficient"
    assert auth.maximum_risk_level is WalletRiskLevel.MEDIUM


def test_lnurl_capabilities_are_independent() -> None:
    raw = _base_raw()
    _add_test_lnurl_wallet(raw)
    registry = _registry(raw)
    assert registry.supports_lnurl_pay("test-lnurl-wallet").compatible is True
    assert registry.supports_lnurl_verify("test-lnurl-wallet").compatible is False
    assert registry.supports_lightning_address("test-lnurl-wallet").compatible is True
    assert registry.supports_lnurl_auth("test-lnurl-wallet", action="login").compatible is True
    assert registry.supports_lnurl_withdraw("test-lnurl-wallet").compatible is True
    assert registry.supports_payerdata_auth("test-lnurl-wallet").compatible is True
    assert registry.supports_success_action("test-lnurl-wallet", "message").compatible is True
    assert registry.supports_success_action("test-lnurl-wallet", "url").state is CapabilityState.PARTIAL


def test_version_constraints_and_unknown_version_are_conservative() -> None:
    raw = _base_raw()
    _add_test_lnurl_wallet(raw)
    registry = _registry(raw)
    assert registry.get_wallet("test-lnurl-wallet", "2.1.0") is not None
    assert registry.get_wallet("test-lnurl-wallet", "1.9.9") is None
    assert registry.resolve_wallet("test-lnurl-wallet", "1.9.9").status.value == "unknown"


def test_malformed_version_fails_safely() -> None:
    raw = _base_raw()
    _add_test_lnurl_wallet(raw)
    registry = _registry(raw)
    assert registry.get_wallet("test-lnurl-wallet", "latest") is None


def test_affected_version_quirk_applied_and_fixed_version_resolved() -> None:
    raw = _base_raw()
    _add_test_lnurl_wallet(raw)
    registry = _registry(raw)
    assert registry.get_known_quirks("test-lnurl-wallet", "2.1.0")
    assert registry.get_known_quirks("test-lnurl-wallet", "2.2.0") == ()


def test_active_critical_quirk_blocks_capability() -> None:
    raw = _base_raw()
    _add_test_lnurl_wallet(raw)
    raw["wallets"][-1]["known_quirks"].append(
        {
            "quirk_id": "critical-bip322-bug",
            "severity": "critical",
            "capability": "bip322",
            "affected_versions": None,
            "description": "Synthetic critical parser bug.",
            "mitigation": "disable_bip322",
            "security_effect": "blocks capability",
            "resolved_in_version": None,
            "active": True,
        }
    )
    result = _registry(raw).supports_bitcoin_proof("test-lnurl-wallet", WalletProofType.BIP322)
    assert result.compatible is False
    assert result.reason_code == "critical_quirk_active"


def test_informational_quirk_does_not_block() -> None:
    raw = _base_raw()
    _add_test_lnurl_wallet(raw)
    raw["wallets"][-1]["known_quirks"] = [
        {
            "quirk_id": "info-only",
            "severity": "informational",
            "capability": "bip322",
            "affected_versions": None,
            "description": "Informational only.",
            "mitigation": "none",
            "security_effect": "none",
            "resolved_in_version": None,
            "active": True,
        }
    ]
    assert _registry(raw).supports_bitcoin_proof("test-lnurl-wallet", WalletProofType.BIP322).compatible


def test_registry_hash_deterministic_ordering_independent_and_changes_on_capability_change() -> None:
    raw = _base_raw()
    reg1 = _registry(raw)
    reg2 = load_wallet_compatibility_yaml_text(yaml.safe_dump(raw, sort_keys=True))
    changed = deepcopy(raw)
    changed["wallets"][0]["bitcoin_capabilities"]["bip322"]["state"] = "supported"
    reg3 = _registry(changed)
    assert reg1.registry_snapshot_hash() == reg2.registry_snapshot_hash()
    assert reg1.registry_snapshot_hash() != reg3.registry_snapshot_hash()


def test_registry_contains_no_user_specific_wallet_data() -> None:
    text = CONFIG_PATH.read_text(encoding="utf-8").lower()
    for forbidden in ("xprv", "mnemonic", "private_key", "wallet_address", "linking_key"):
        assert forbidden not in text


def test_query_results_contain_no_user_specific_wallet_data() -> None:
    result = _registry().supports_lnurl_auth("missing-wallet", action="login")
    serialized = repr(result).lower()
    for forbidden in ("bitcoin_address", "linking_key", "signature", "seed", "xprv"):
        assert forbidden not in serialized
