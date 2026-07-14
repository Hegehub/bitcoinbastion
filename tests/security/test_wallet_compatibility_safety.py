from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import yaml

from app.domain.wallet_auth.proofs import WalletProofType, WalletVerificationStrength
from app.domain.wallet_auth.risks import WalletRiskLevel
from app.services.wallet_auth.compatibility_loader import load_wallet_compatibility_yaml_text
from app.services.wallet_auth.wallet_compatibility import CompatibilityQuery

CONFIG_PATH = Path("config/wallet_auth_compatibility.yaml")


def _base_raw() -> dict:
    return yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))


def _registry(raw: dict | None = None):
    return load_wallet_compatibility_yaml_text(yaml.safe_dump(raw or _base_raw(), sort_keys=False))


def test_wallet_name_alone_cannot_authorize_access() -> None:
    result = _registry().supports_bitcoin_proof("generic-legacy-message-wallet", WalletProofType.LEGACY_MESSAGE_SIGNATURE)
    assert not hasattr(result, "authorized")
    assert not hasattr(result, "access_granted")
    assert "registry_is_not_authorization" in result.limitations


def test_client_declared_support_cannot_override_registry() -> None:
    result = _registry().evaluate_action_compatibility(
        CompatibilityQuery(
            wallet_slug="generic-unknown-wallet",
            capability="bip322",
            proof_type=WalletProofType.BIP322,
            client_claims={"bip322": True, "hardware_wallet": True},
        )
    )
    assert result.compatible is False
    assert result.maximum_verification_strength is WalletVerificationStrength.COMPATIBILITY


def test_client_declared_hardware_flag_cannot_grant_high_assurance() -> None:
    result = _registry().evaluate_action_compatibility(
        CompatibilityQuery(
            wallet_slug="missing-wallet",
            capability="hardware_wallet",
            requested_risk_level=WalletRiskLevel.CRITICAL,
            client_claims={"hardware_wallet": True, "assurance": "sovereign"},
        )
    )
    assert result.compatible is False
    assert result.maximum_verification_strength is WalletVerificationStrength.COMPATIBILITY


def test_unknown_wallet_fails_closed_for_critical_actions() -> None:
    result = _registry().evaluate_action_compatibility(
        CompatibilityQuery(
            wallet_slug="unknown-by-name",
            capability="treasury_policy_change",
            requested_risk_level=WalletRiskLevel.CRITICAL,
        )
    )
    assert result.compatible is False
    assert result.maximum_risk_level is WalletRiskLevel.LOW


def test_blocked_wallet_cannot_be_considered_eligible() -> None:
    raw = _base_raw()
    blocked = deepcopy(raw["wallets"][0])
    blocked["wallet_slug"] = "blocked-wallet"
    blocked["registry_id"] = "blocked-wallet-v1"
    blocked["status"] = "blocked"
    blocked["security"]["eligible_for_routine_login"] = False
    raw["wallets"].append(blocked)
    result = _registry(raw).supports_lnurl_auth("blocked-wallet", action="login")
    assert result.compatible is False
    assert result.reason_code == "wallet_blocked"


def test_legacy_signature_wallet_cannot_satisfy_high_risk_action() -> None:
    result = _registry().evaluate_action_compatibility(
        CompatibilityQuery(
            wallet_slug="generic-legacy-message-wallet",
            capability="create_api_key",
            proof_type=WalletProofType.LEGACY_MESSAGE_SIGNATURE,
            requested_risk_level=WalletRiskLevel.HIGH,
        )
    )
    assert result.compatible is False
    assert result.reason_code == "additional_bip322_required"


def test_lnurl_auth_capability_is_not_onchain_ownership_proof() -> None:
    result = _registry().supports_lnurl_auth("generic-unknown-wallet", action="login")
    assert "runtime_proof_verification_required" in result.limitations
    assert not hasattr(result, "onchain_ownership_verified")


def test_lnurl_pay_capability_is_not_payment_settlement() -> None:
    result = _registry().supports_lnurl_pay("generic-unknown-wallet")
    assert not hasattr(result, "payment_settled")
    assert "registry_is_not_authorization" in result.limitations


def test_lightning_address_is_not_principal_identity() -> None:
    result = _registry().supports_lightning_address("generic-unknown-wallet")
    assert not hasattr(result, "principal_identity")
    assert "registry_is_not_authorization" in result.limitations


def test_lnurl_withdraw_capability_is_not_payout_authorization() -> None:
    result = _registry().supports_lnurl_withdraw("generic-unknown-wallet")
    assert not hasattr(result, "payout_authorized")
    assert result.compatible is False


def test_compatibility_results_do_not_expose_secret_user_data() -> None:
    result = _registry().evaluate_action_compatibility(
        CompatibilityQuery(
            wallet_slug="missing-wallet",
            capability="login",
            client_claims={"wallet_address": "bc1qexample", "signature": "MEUCIQ..."},
        )
    )
    rendered = repr(result).lower()
    for forbidden in ("bc1qexample", "meuciq", "wallet_address", "signature", "seed", "xprv"):
        assert forbidden not in rendered
