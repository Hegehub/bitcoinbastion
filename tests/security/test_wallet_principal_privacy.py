from __future__ import annotations

import asyncio
import logging
from dataclasses import fields
from datetime import UTC, datetime

import pytest

from app.domain.wallet_auth.networks import WalletNetwork
from app.domain.wallet_auth.proofs import WalletProofType, WalletScriptType, WalletVerificationStrength
from app.services.wallet_auth.principal_service import PrincipalService, WalletPrincipalPrivacyViolationError
from app.services.wallet_auth.principal_types import (
    PrincipalCreationResult,
    PrincipalPolicyContext,
    PrincipalType,
    VerifiedWalletProof,
)
from app.services.wallet_auth.privacy_commitments import compute_hmac_lookup_hash, compute_sha256_commitment


def _proof_with_raw_address_for_memory() -> VerifiedWalletProof:
    return VerifiedWalletProof(
        proof_type=WalletProofType.BIP322,
        normalized_wallet_identifier="bc1qtestaddressnotreturned",
        wallet_identifier_commitment=compute_hmac_lookup_hash("test-pepper", "address", "bc1qtestaddressnotreturned"),
        network=WalletNetwork.BITCOIN_MAINNET,
        script_type=WalletScriptType.P2WPKH,
        verification_strength=WalletVerificationStrength.STANDARD,
        verified_at=datetime.now(UTC),
        proof_hash=compute_sha256_commitment("proof-material"),
        verifier_name="test-verifier",
        verifier_version="1",
        script_pubkey_hash=compute_sha256_commitment("script"),
    )


def test_raw_address_absent_from_serialized_service_results() -> None:
    async def run() -> None:
        service = PrincipalService(server_pepper="principal-test-pepper")
        result = await service.find_or_create_bitcoin_principal(proof=_proof_with_raw_address_for_memory())
        policy = await service.build_policy_actor_context(result.principal_hash)
        rendered = f"{result.safe_summary()!r} {policy.as_dict()!r}".lower()
        assert "bc1qtestaddressnotreturned" not in rendered
        assert "wallet_identifier" not in rendered

    asyncio.run(run())


def test_raw_address_and_signature_absent_from_logs(caplog: pytest.LogCaptureFixture) -> None:
    async def run() -> None:
        service = PrincipalService(server_pepper="principal-test-pepper")
        with caplog.at_level(logging.INFO):
            await service.find_or_create_bitcoin_principal(proof=_proof_with_raw_address_for_memory())
        rendered = caplog.text.lower()
        assert "bc1qtestaddressnotreturned" not in rendered
        assert "signature" not in rendered

    asyncio.run(run())


def test_raw_address_cannot_be_principal_hash() -> None:
    async def run() -> None:
        service = PrincipalService(server_pepper="principal-test-pepper")
        with pytest.raises(WalletPrincipalPrivacyViolationError):
            await service.find_principal_by_hash("bc1qtestaddressnotprincipal")

    asyncio.run(run())


def test_email_cannot_be_principal_identity() -> None:
    with pytest.raises(ValueError):
        _ = VerifiedWalletProof(
            proof_type=WalletProofType.BIP322,
            normalized_wallet_identifier="alice@example.com",
            wallet_identifier_commitment=compute_hmac_lookup_hash("test-pepper", "address", "alice"),
            network=WalletNetwork.BITCOIN_MAINNET,
            script_type=WalletScriptType.P2WPKH,
            verification_strength=WalletVerificationStrength.STANDARD,
            verified_at=datetime.now(UTC),
            proof_hash=compute_sha256_commitment("proof"),
            verifier_name="test-verifier",
            verifier_version="1",
        )


def test_lightning_address_cannot_be_bitcoin_principal_identity() -> None:
    with pytest.raises(ValueError):
        _ = VerifiedWalletProof(
            proof_type=WalletProofType.BIP322,
            normalized_wallet_identifier="wallet@example.org",
            wallet_identifier_commitment=compute_hmac_lookup_hash("test-pepper", "address", "wallet"),
            network=WalletNetwork.BITCOIN_MAINNET,
            script_type=WalletScriptType.P2WPKH,
            verification_strength=WalletVerificationStrength.STANDARD,
            verified_at=datetime.now(UTC),
            proof_hash=compute_sha256_commitment("proof"),
            verifier_name="test-verifier",
            verifier_version="1",
        )


def test_no_global_user_id_field_is_introduced() -> None:
    checked = (VerifiedWalletProof, PrincipalCreationResult, PrincipalPolicyContext)
    for cls in checked:
        assert "global_user_id" not in {field.name for field in fields(cls)}


def test_no_bitcoin_seed_or_private_key_handling_exists() -> None:
    field_names = {field.name for field in fields(VerifiedWalletProof)}
    forbidden = {"seed", "wallet_seed", "bitcoin_seed", "private_key", "mnemonic", "xprv"}
    assert field_names.isdisjoint(forbidden)


def test_lightning_principal_namespace_is_separate_extension_path() -> None:
    service = PrincipalService(server_pepper="principal-test-pepper")
    commitment = compute_hmac_lookup_hash("test-pepper", "address", "same-material")
    bitcoin_hash = service.derive_principal_hash(
        principal_type=PrincipalType.BITCOIN_WALLET_PRINCIPAL,
        wallet_identifier_commitment=commitment,
        network=WalletNetwork.BITCOIN_MAINNET,
    )
    lightning_hash = service.derive_principal_hash(
        principal_type=PrincipalType.LIGHTNING_WALLET_PRINCIPAL,
        wallet_identifier_commitment=commitment,
        network=WalletNetwork.BITCOIN_MAINNET,
    )
    assert bitcoin_hash != lightning_hash
