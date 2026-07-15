"""Tests for Wallet-first and LNURL SQLAlchemy model definitions."""

from __future__ import annotations

import importlib
from typing import Iterable

from sqlalchemy import inspect

from app.db.models import lnurl as lnurl_models
from app.db.models import wallet_auth as wallet_models
from app.db.models.lnurl import (
    LNURLAuthChallenge,
    LNURLAuthAttempt,
    LNURLInvoice,
    LNURLPayRequest,
    LNURLPayerData,
    LNURLPaymentProof,
    LNURLPrincipal,
    LNURLReceiptPacket,
    LNURLSuccessAction,
    LNURLVerifyCheck,
    LNURLWithdrawAttempt,
    LNURLWithdrawRequest,
    LightningAddress,
    PayRegisterLNURLBinding,
)
from app.db.models.wallet_auth import (
    MultiWalletQuorum,
    RecoveryCapsule,
    WalletDevice,
    WalletPrincipal,
    WalletPrivacyCommitment,
    WalletProof,
    WalletSession,
    WalletSessionNonce,
    WalletStepUpProof,
)

FORBIDDEN_COLUMN_NAMES = {
    "password",
    "password_hash",
    "email_required",
    "raw_address",
    "raw_key",
    "raw_k1",
    "raw_seed",
    "mnemonic",
    "xprv",
    "private_key",
    "bearer_token",
    "access_token",
    "raw_session",
    "raw_access_pass",
    "raw_recovery_phrase",
}

MODEL_CLASSES = [
    WalletPrincipal,
    WalletProof,
    WalletDevice,
    WalletSession,
    WalletSessionNonce,
    WalletStepUpProof,
    RecoveryCapsule,
    MultiWalletQuorum,
    WalletPrivacyCommitment,
    LNURLAuthChallenge,
    LNURLAuthAttempt,
    LNURLPrincipal,
    LNURLPayRequest,
    LNURLInvoice,
    LNURLPaymentProof,
    LNURLVerifyCheck,
    LNURLWithdrawRequest,
    LNURLWithdrawAttempt,
    LNURLSuccessAction,
    LNURLPayerData,
    LightningAddress,
    LNURLReceiptPacket,
    PayRegisterLNURLBinding,
]


def column_names(model: type[object]) -> set[str]:
    return {column.name for column in inspect(model).columns}


def assert_has_columns(model: type[object], expected: Iterable[str]) -> None:
    assert set(expected).issubset(column_names(model))


def test_wallet_lnurl_model_modules_import_safely() -> None:
    assert importlib.import_module("app.db.models.wallet_auth") is wallet_models
    assert importlib.import_module("app.db.models.lnurl") is lnurl_models


def test_models_do_not_define_forbidden_secret_or_classic_auth_columns() -> None:
    for model in MODEL_CLASSES:
        assert FORBIDDEN_COLUMN_NAMES.isdisjoint(column_names(model)), model.__name__


def test_required_wallet_principal_columns_exist() -> None:
    assert_has_columns(WalletPrincipal, {"principal_hash", "principal_type", "status"})


def test_required_lnurl_auth_challenge_columns_exist() -> None:
    assert_has_columns(LNURLAuthChallenge, {"k1_hash", "action", "auth_domain", "status", "expires_at"})


def test_required_lnurl_pay_request_columns_exist() -> None:
    assert_has_columns(LNURLPayRequest, {"payment_id_hash", "amount_msat", "metadata_hash", "status"})


def test_required_lnurl_withdraw_request_columns_exist() -> None:
    assert_has_columns(
        LNURLWithdrawRequest,
        {"k1_hash", "min_withdrawable_msat", "max_withdrawable_msat", "policy_hash", "status"},
    )


def test_required_lightning_address_columns_exist() -> None:
    assert_has_columns(LightningAddress, {"address_hash", "name_hash", "domain", "status"})


def test_hash_first_lookup_fields_are_present() -> None:
    assert_has_columns(WalletPrincipal, {"principal_hash", "address_hash", "script_pubkey_hash", "lnurl_key_hash"})
    assert_has_columns(WalletProof, {"proof_hash", "challenge_hash", "key_fingerprint"})
    assert_has_columns(WalletSession, {"session_hash", "session_public_key_fingerprint", "device_key_fingerprint"})
    assert_has_columns(WalletSessionNonce, {"session_hash", "nonce_hash", "request_digest_hash"})
    assert_has_columns(LNURLAuthChallenge, {"challenge_hash", "k1_hash", "callback_url_hash"})
    assert_has_columns(LNURLAuthAttempt, {"k1_hash", "key_hash", "sig_hash"})
    assert_has_columns(LNURLPaymentProof, {"payment_id_hash", "invoice_hash", "payment_hash", "preimage_hash"})
    assert_has_columns(LNURLWithdrawRequest, {"withdraw_id_hash", "k1_hash", "callback_hash"})


def test_metadata_columns_exist_for_redacted_operational_context() -> None:
    for model in MODEL_CLASSES:
        assert "metadata_json" in column_names(model), model.__name__


def test_prompt_adds_models_only_not_migration_functions() -> None:
    assert not hasattr(wallet_models, "upgrade")
    assert not hasattr(wallet_models, "downgrade")
    assert not hasattr(lnurl_models, "upgrade")
    assert not hasattr(lnurl_models, "downgrade")
