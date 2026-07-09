from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from app.domain.lnurl import LNURLAuthAction, LNURLSuccessActionType
from app.domain.wallet_auth import (
    WalletAuthAction,
    WalletDeviceClass,
    WalletNetwork,
    WalletPrincipalActorType,
    WalletPrincipalStatus,
    WalletProofType,
    WalletRecoveryProfile,
    WalletRiskLevel,
    WalletVerificationStrength,
)
from app.schemas import lnurl as lnurl_schemas
from app.schemas import wallet_auth as wallet_schemas


def _future() -> datetime:
    return datetime.now(UTC) + timedelta(minutes=5)


def _hex_k1() -> str:
    return "ab" * 32


def _field_names(model: type) -> set[str]:
    return set(model.model_fields)


def test_wallet_schemas_do_not_include_classic_auth_or_wallet_secret_fields() -> None:
    forbidden = {"password", "seed", "private_key", "mnemonic", "xprv", "access_token", "bearer_token", "user_id"}
    wallet_models = [
        wallet_schemas.WalletAuthChallengeCreate,
        wallet_schemas.WalletRegisterRequest,
        wallet_schemas.WalletLoginRequest,
        wallet_schemas.WalletPrincipalResponse,
        wallet_schemas.WalletSessionCreate,
        wallet_schemas.WalletSessionResponse,
        wallet_schemas.WalletEntitlementResponse,
    ]
    for model in wallet_models:
        assert forbidden.isdisjoint(_field_names(model))


def test_wallet_register_and_login_do_not_require_email_or_password() -> None:
    register = wallet_schemas.WalletRegisterRequest(
        challenge_id="chal_1",
        proof_type=WalletProofType.BIP322,
        wallet_identifier="bc1qexampleproofinput",
        signature="signature",
        public_key=None,
        device_key_fingerprint="dev_fp",
        device_class=WalletDeviceClass.DESKTOP_VAULT,
        origin="https://app.example",
        network=WalletNetwork.BITCOIN_MAINNET,
        wallet_name=None,
    )
    login = wallet_schemas.WalletLoginRequest(
        challenge_id="chal_1",
        proof_type=WalletProofType.BIP322,
        wallet_identifier="bc1qexampleproofinput",
        signature="signature",
        public_key=None,
        device_key_fingerprint="dev_fp",
        origin="https://app.example",
        network=WalletNetwork.BITCOIN_MAINNET,
    )
    assert register.device_key_fingerprint == "dev_fp"
    assert login.proof_type is WalletProofType.BIP322


def test_wallet_session_response_is_pop_not_bearer_token() -> None:
    response = wallet_schemas.WalletSessionResponse(
        session_token="sess_once",
        principal_hash="principal_hash",
        device_key_fingerprint="dev_fp",
        scopes=["market:read"],
        metric_groups=["market"],
        expires_at=_future(),
        issued_at=datetime.now(UTC),
        policy_mode="proof_of_possession",
    )
    assert response.session_type == "pop"
    assert response.requires_request_signature is True
    assert "bearer_token" not in _field_names(wallet_schemas.WalletSessionResponse)


def test_wallet_principal_and_entitlement_responses_use_hashes_not_identity() -> None:
    principal = wallet_schemas.WalletPrincipalResponse(
        principal_hash="principal_hash",
        principal_type="bitcoin_wallet_principal",
        actor_type=WalletPrincipalActorType.BITCOIN_WALLET_PRINCIPAL,
        status=WalletPrincipalStatus.ACTIVE,
        verification_strength=WalletVerificationStrength.STANDARD,
        network=WalletNetwork.BITCOIN_MAINNET,
        proof_method=WalletProofType.BIP322,
        address_hash="addr_hash",
        script_pubkey_hash="spk_hash",
        lnurl_key_hash=None,
        auth_domain=None,
        created_at=datetime.now(UTC),
    )
    entitlement = wallet_schemas.WalletEntitlementResponse(
        principal_hash="principal_hash",
        actor_type=WalletPrincipalActorType.BITCOIN_WALLET_PRINCIPAL,
        plan_code="pro",
        status="active",
        scopes=["market:read"],
        metric_groups=["market"],
        limits={},
        valid_from=datetime.now(UTC),
        valid_until=_future(),
    )
    assert principal.address_hash == "addr_hash"
    assert "wallet_identifier" not in _field_names(wallet_schemas.WalletPrincipalResponse)
    assert "user_id" not in _field_names(wallet_schemas.WalletPrincipalResponse)
    assert entitlement.principal_hash == "principal_hash"
    assert "user_id" not in _field_names(wallet_schemas.WalletEntitlementResponse)


def test_wallet_schema_validators_reject_forbidden_metadata_and_broad_scopes() -> None:
    with pytest.raises(ValidationError):
        wallet_schemas.WalletAuthChallengeCreate(
            action=WalletAuthAction.LOGIN,
            network=WalletNetwork.BITCOIN_MAINNET,
            origin="https://app.example",
            requested_scopes=["api:all"],
        )
    with pytest.raises(ValidationError):
        wallet_schemas.WalletAuthChallengeCreate(
            action=WalletAuthAction.LOGIN,
            network=WalletNetwork.BITCOIN_MAINNET,
            origin="https://app.example",
            metadata={"seed": "never"},
        )
    with pytest.raises(ValidationError):
        wallet_schemas.WalletAuthChallengeCreate(
            action=WalletAuthAction.TREASURY_POLICY_CHANGE,
            network=WalletNetwork.BITCOIN_MAINNET,
            origin="https://app.example",
            risk_level=WalletRiskLevel.LOW,
        )


def test_wallet_recovery_rejects_secret_factor_terms() -> None:
    wallet_schemas.WalletRecoveryStartRequest(
        principal_hash="principal_hash",
        recovery_profile=WalletRecoveryProfile.PLUS_PRO,
        proof_type=WalletProofType.BIP322,
        lnurl_auth_requested=True,
    )
    with pytest.raises(ValidationError):
        wallet_schemas.WalletRecoveryCompleteRequest(
            recovery_attempt_id="rec_1",
            principal_hash="principal_hash",
            factors=[{"mnemonic": "never"}],
            step_up_id=None,
            cooldown_acknowledged=True,
        )


def test_lnurl_auth_schemas_include_challenge_and_callback_fields() -> None:
    challenge = lnurl_schemas.LNURLAuthChallengeResponse(
        challenge_id="ln_chal",
        k1=_hex_k1(),
        action=LNURLAuthAction.AUTH,
        callback_url="https://auth.example/callback",
        lnurl_bech32="lnurl1example",
        domain="auth.example",
        expires_at=_future(),
    )
    callback = lnurl_schemas.LNURLAuthCallbackRequest(k1=_hex_k1(), key="02" + "11" * 32, sig="3044")
    assert challenge.k1 == _hex_k1()
    assert challenge.callback_url
    assert challenge.lnurl_bech32
    assert callback.key.startswith("02")


def test_lnurl_pay_request_callback_and_verify_schemas() -> None:
    pay_request = lnurl_schemas.LNURLPayRequestResponse(
        callback="https://pay.example/callback",
        min_sendable=1_000,
        max_sendable=2_000,
        metadata='[["text/plain","Pro subscription"]]',
        comment_allowed=140,
    )
    callback_response = lnurl_schemas.LNURLPayCallbackResponse(
        pr="lnbc1invoice",
        verify="https://pay.example/verify/payment_1",
        success_action={"tag": "message", "message": "Pro Pass activated"},
    )
    verify_response = lnurl_schemas.LNURLVerifyResponse(settled=False)
    assert pay_request.tag == "payRequest"
    assert callback_response.pr == "lnbc1invoice"
    assert callback_response.verify is not None
    assert callback_response.success_action is not None
    assert verify_response.settled is False


def test_lnurl_lightning_address_and_withdraw_schemas() -> None:
    pay = lnurl_schemas.LNURLPayRequestResponse(
        callback="https://pay.example/callback",
        min_sendable=1_000,
        max_sendable=2_000,
        metadata='[["text/plain","Lite"]]',
    )
    address = lnurl_schemas.LightningAddressResponse(
        username="lite",
        domain="bitcoin-bastion.com",
        address="lite@bitcoin-bastion.com",
        lnurl_pay=pay,
        product_code="lite",
        merchant_id_hash=None,
        terminal_id_hash=None,
    )
    withdraw = lnurl_schemas.LNURLWithdrawRequestResponse(
        callback="https://withdraw.example/callback",
        k1=_hex_k1(),
        default_description="refund",
        min_withdrawable=1_000,
        max_withdrawable=2_000,
        expires_at=_future(),
        policy_approved=True,
    )
    assert "user_id" not in _field_names(lnurl_schemas.LightningAddressResponse)
    assert address.address == "lite@bitcoin-bastion.com"
    assert withdraw.tag == "withdrawRequest"
    assert withdraw.policy_approved is True


def test_lnurl_payerdata_auth_without_email_and_success_action_safety() -> None:
    payerdata = lnurl_schemas.LNURLPayerDataRequest(auth={"mandatory": False})
    assert payerdata.auth is not None
    assert payerdata.email is None
    action = lnurl_schemas.LNURLSuccessAction(
        tag=LNURLSuccessActionType.URL.value,
        url="https://app.example/activate?id=activation_ref",
    )
    assert action.url is not None
    with pytest.raises(ValidationError):
        lnurl_schemas.LNURLSuccessAction(
            tag=LNURLSuccessActionType.URL.value,
            url="https://app.example/activate?session_token=raw",
        )


def test_lnurl_comment_and_amount_validation_are_not_authorization() -> None:
    callback = lnurl_schemas.LNURLPayCallbackRequest(payment_id="pay_1", amount=1_000, comment="order reference")
    assert callback.comment == "order reference"
    with pytest.raises(ValidationError):
        lnurl_schemas.LNURLPayCallbackRequest(payment_id="pay_1", amount=1_000, comment="x" * 1_001)
    with pytest.raises(ValidationError):
        lnurl_schemas.LNURLPayRequestResponse(
            callback="https://pay.example/callback",
            min_sendable=2_000,
            max_sendable=1_000,
            metadata='[["text/plain","bad"]]',
        )


def test_lnurl_principal_response_has_no_raw_key_or_user_id() -> None:
    principal = lnurl_schemas.LightningPrincipalResponse(
        principal_hash="principal_hash",
        lnurl_key_hash="key_hash",
        auth_domain="auth.example",
        verification_strength=WalletVerificationStrength.STANDARD,
        status=WalletPrincipalStatus.ACTIVE,
        created_at=datetime.now(UTC),
        per_product_alias="alias",
    )
    assert principal.lnurl_key_hash == "key_hash"
    assert "key" not in _field_names(lnurl_schemas.LightningPrincipalResponse)
    assert "user_id" not in _field_names(lnurl_schemas.LightningPrincipalResponse)


def test_no_token_response_or_bearer_semantics_introduced() -> None:
    assert not hasattr(wallet_schemas, "TokenResponse")
    assert not hasattr(lnurl_schemas, "TokenResponse")
    assert "bearer_token" not in _field_names(wallet_schemas.WalletSessionResponse)


def test_schema_imports_are_side_effect_safe(monkeypatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("REDIS_URL", raising=False)
    assert wallet_schemas.WalletAuthChallengeCreate is not None
    assert lnurl_schemas.LNURLAuthChallengeCreate is not None
    assert not hasattr(wallet_schemas, "FastAPI")
    assert not hasattr(lnurl_schemas, "FastAPI")
