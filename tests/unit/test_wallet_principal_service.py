from __future__ import annotations

import asyncio
from dataclasses import fields, replace
from datetime import UTC, datetime
import pytest

from app.domain.wallet_auth.networks import WalletNetwork
from app.domain.wallet_auth.principals import WalletPrincipalStatus
from app.domain.wallet_auth.proofs import WalletProofType, WalletScriptType, WalletVerificationStrength
from app.services.wallet_auth.principal_service import (
    PrincipalService,
    WalletPrincipalAlreadyRevokedError,
    WalletPrincipalInvalidTransitionError,
    WalletPrincipalNetworkMismatchError,
    WalletPrincipalProofRequiredError,
)
from app.services.wallet_auth.principal_types import PrincipalType, VerifiedWalletProof
from app.services.wallet_auth.privacy_commitments import compute_hmac_lookup_hash, compute_sha256_commitment


class FakeRevocationRegistry:
    def __init__(self) -> None:
        self.revoked: set[tuple[str, str]] = set()
        self.calls: list[dict[str, object]] = []

    def is_revoked(self, *, target_type: str, target_hash: str) -> bool:
        return (target_type, target_hash) in self.revoked

    def revoke(self, *, target_type: str, target_hash: str, reason_code: str, policy_epoch: int) -> None:
        self.revoked.add((target_type, target_hash))
        self.calls.append(
            {
                "target_type": target_type,
                "target_hash": target_hash,
                "reason_code": reason_code,
                "policy_epoch": policy_epoch,
            }
        )


def _proof(
    *,
    network: WalletNetwork = WalletNetwork.BITCOIN_MAINNET,
    commitment_seed: str = "wallet-a",
    proof_type: WalletProofType = WalletProofType.BIP322,
    strength: WalletVerificationStrength = WalletVerificationStrength.STANDARD,
    proof_seed: str = "proof-a",
) -> VerifiedWalletProof:
    return VerifiedWalletProof(
        proof_type=proof_type,
        normalized_wallet_identifier=f"wallet-fixture-{commitment_seed}",
        wallet_identifier_commitment=compute_hmac_lookup_hash("test-pepper", "address", commitment_seed),
        network=network,
        script_type=WalletScriptType.P2WPKH,
        verification_strength=strength,
        verified_at=datetime.now(UTC),
        proof_hash=compute_sha256_commitment(proof_seed),
        verifier_name="test-verifier",
        verifier_version="1",
        limitations=("policy_engine_required",),
        policy_hints=("device_binding_required",),
        script_pubkey_hash=compute_sha256_commitment(f"script-{commitment_seed}"),
        action="login",
        policy_hash=compute_sha256_commitment("policy"),
    )


def _service(
    audit: list[tuple[str, dict[str, object]]] | None = None,
    revocation: FakeRevocationRegistry | None = None,
) -> PrincipalService:
    emitter = (lambda event, payload: audit.append((event, payload))) if audit is not None else None
    return PrincipalService(server_pepper="principal-test-pepper", audit_emitter=emitter, revocation_registry=revocation)


def test_valid_trusted_bip322_proof_creates_bitcoin_wallet_principal() -> None:
    async def run() -> None:
        result = await _service().find_or_create_bitcoin_principal(proof=_proof())
        assert result.created is True
        assert result.principal_type is PrincipalType.BITCOIN_WALLET_PRINCIPAL
        assert result.status is WalletPrincipalStatus.ACTIVE
        assert result.proof_method is WalletProofType.BIP322
        assert result.verification_strength is WalletVerificationStrength.STANDARD
        assert result.principal_hash.startswith("hmac-sha256:")

    asyncio.run(run())


def test_created_result_does_not_expose_raw_address() -> None:
    async def run() -> None:
        result = await _service().find_or_create_bitcoin_principal(proof=_proof(commitment_seed="not-raw-address"))
        rendered = repr(result.safe_summary()).lower()
        assert "bc1" not in rendered
        assert "wallet-fixture" not in rendered
        assert "private" not in rendered

    asyncio.run(run())


def test_repeated_proof_returns_same_principal_idempotently() -> None:
    async def run() -> None:
        service = _service()
        proof = _proof()
        first = await service.find_or_create_bitcoin_principal(proof=proof)
        second = await service.find_or_create_bitcoin_principal(proof=replace(proof, proof_hash=compute_sha256_commitment("proof-b")))
        assert first.principal_hash == second.principal_hash
        assert first.created is True
        assert second.created is False

    asyncio.run(run())


def test_different_networks_create_different_principals() -> None:
    async def run() -> None:
        service = _service()
        mainnet = await service.find_or_create_bitcoin_principal(proof=_proof(network=WalletNetwork.BITCOIN_MAINNET))
        testnet = await service.find_or_create_bitcoin_principal(proof=_proof(network=WalletNetwork.BITCOIN_TESTNET))
        assert mainnet.principal_hash != testnet.principal_hash

    asyncio.run(run())


def test_different_wallet_commitments_create_different_principals() -> None:
    async def run() -> None:
        service = _service()
        first = await service.find_or_create_bitcoin_principal(proof=_proof(commitment_seed="wallet-a"))
        second = await service.find_or_create_bitcoin_principal(proof=_proof(commitment_seed="wallet-b"))
        assert first.principal_hash != second.principal_hash

    asyncio.run(run())


def test_unverified_or_arbitrary_boolean_input_is_rejected() -> None:
    async def run() -> None:
        with pytest.raises(WalletPrincipalProofRequiredError):
            await _service().find_or_create_bitcoin_principal(proof={"verified": True})  # type: ignore[arg-type]

    asyncio.run(run())


def test_raw_wallet_address_alone_is_insufficient() -> None:
    async def run() -> None:
        with pytest.raises(WalletPrincipalProofRequiredError):
            await _service().create_bitcoin_principal(proof="bc1qnotproof")  # type: ignore[arg-type]

    asyncio.run(run())


def test_principal_state_machine_transitions() -> None:
    async def run() -> None:
        service = _service()
        result = await service.find_or_create_bitcoin_principal(proof=_proof())
        record = await service.get_principal(result.principal_hash)
        await service.repository.update(replace(record, status=WalletPrincipalStatus.PENDING_VERIFICATION))
        activated = await service.activate_principal(result.principal_hash, reason_code="proof_complete")
        assert activated.previous_status is WalletPrincipalStatus.PENDING_VERIFICATION
        suspended = await service.suspend_principal(result.principal_hash, reason_code="operator_hold")
        assert suspended.new_status is WalletPrincipalStatus.SUSPENDED
        reactivated = await service.activate_principal(result.principal_hash, reason_code="hold_cleared")
        assert reactivated.new_status is WalletPrincipalStatus.ACTIVE
        locked = await service.recovery_lock_principal(result.principal_hash, reason_code="recovery_started")
        assert locked.new_status is WalletPrincipalStatus.RECOVERY_LOCKED
        with pytest.raises(WalletPrincipalInvalidTransitionError):
            await service.activate_principal(result.principal_hash, reason_code="ordinary_activation")
        revoked = await service.revoke_principal(result.principal_hash, reason_code="principal_compromised")
        assert revoked.new_status is WalletPrincipalStatus.REVOKED
        with pytest.raises(WalletPrincipalInvalidTransitionError):
            await service.activate_principal(result.principal_hash, reason_code="reactivate_revoked")

    asyncio.run(run())


def test_proof_association_and_duplicate_proof_are_safe() -> None:
    async def run() -> None:
        service = _service()
        result = await service.find_or_create_bitcoin_principal(proof=_proof())
        methods = await service.list_principal_proof_methods(result.principal_hash)
        assert methods == (WalletProofType.BIP322,)
        added = await service.associate_wallet_proof(principal_hash=result.principal_hash, proof=_proof())
        assert added is False

    asyncio.run(run())


def test_weak_proof_does_not_downgrade_highest_assurance() -> None:
    async def run() -> None:
        service = _service()
        high = await service.find_or_create_bitcoin_principal(
            proof=_proof(strength=WalletVerificationStrength.HIGH_ASSURANCE, proof_seed="high")
        )
        weak_proof = _proof(
            proof_type=WalletProofType.LEGACY_MESSAGE_SIGNATURE,
            strength=WalletVerificationStrength.COMPATIBILITY,
            proof_seed="legacy",
        )
        await service.record_successful_verification(high.principal_hash, proof=weak_proof)
        record = await service.get_principal(high.principal_hash)
        assert record.current_proof_strength is WalletVerificationStrength.COMPATIBILITY
        assert record.highest_verified_strength is WalletVerificationStrength.HIGH_ASSURANCE

    asyncio.run(run())


def test_legacy_signature_remains_compatibility_level() -> None:
    async def run() -> None:
        legacy = _proof(
            proof_type=WalletProofType.LEGACY_MESSAGE_SIGNATURE,
            strength=WalletVerificationStrength.COMPATIBILITY,
        )
        result = await _service().find_or_create_bitcoin_principal(proof=legacy)
        assert result.verification_strength is WalletVerificationStrength.COMPATIBILITY

    asyncio.run(run())


def test_proof_network_mismatch_rejected() -> None:
    async def run() -> None:
        service = _service()
        result = await service.find_or_create_bitcoin_principal(proof=_proof(network=WalletNetwork.BITCOIN_MAINNET))
        mismatched = _proof(network=WalletNetwork.BITCOIN_TESTNET)
        with pytest.raises(WalletPrincipalNetworkMismatchError):
            await service.record_successful_verification(result.principal_hash, proof=mismatched)

    asyncio.run(run())


def test_concurrent_find_or_create_does_not_duplicate_principals() -> None:
    async def run() -> None:
        service = _service()
        proof = _proof()
        results = await asyncio.gather(
            service.find_or_create_bitcoin_principal(proof=proof),
            service.find_or_create_bitcoin_principal(proof=replace(proof, proof_hash=compute_sha256_commitment("race-proof"))),
        )
        assert results[0].principal_hash == results[1].principal_hash
        assert sum(1 for result in results if result.created) == 1

    asyncio.run(run())


def test_audit_events_are_emitted_without_raw_material() -> None:
    async def run() -> None:
        audit: list[tuple[str, dict[str, object]]] = []
        service = _service(audit=audit)
        result = await service.find_or_create_bitcoin_principal(proof=_proof())
        await service.suspend_principal(result.principal_hash, reason_code="operator_hold")
        await service.revoke_principal(result.principal_hash, reason_code="principal_compromised")
        event_names = [name for name, _ in audit]
        assert "wallet_principal_created" in event_names
        assert "wallet_proof_associated" in event_names
        assert "wallet_principal_suspended" in event_names
        assert "wallet_principal_revoked" in event_names
        rendered = repr(audit).lower()
        assert "wallet-fixture" not in rendered
        assert "signature" not in rendered
        assert "private" not in rendered

    asyncio.run(run())


def test_revocation_status_and_registry_hook() -> None:
    async def run() -> None:
        revocation = FakeRevocationRegistry()
        service = _service(revocation=revocation)
        result = await service.find_or_create_bitcoin_principal(proof=_proof())
        await service.revoke_principal(result.principal_hash, reason_code="principal_compromised")
        with pytest.raises(WalletPrincipalAlreadyRevokedError):
            await service.verify_principal_status(result.principal_hash)
        await service.revoke_principal(result.principal_hash, reason_code="principal_compromised")
        assert len(revocation.calls) == 1

    asyncio.run(run())


def test_policy_and_device_contexts_do_not_claim_authorization() -> None:
    async def run() -> None:
        service = _service()
        result = await service.find_or_create_bitcoin_principal(proof=_proof())
        policy = await service.build_policy_actor_context(result.principal_hash)
        device = await service.prepare_device_binding_context(result.principal_hash)
        data = policy.as_dict()
        assert data["actor_type"] == "bitcoin_wallet_principal"
        assert data["device_bound"] is False
        assert data["session_active"] is False
        assert data["entitlement_status"] == "unknown"
        assert "allowed" not in data
        assert device.allowed_binding_methods == ("device_key", "hardware_evidence_step_up")

    asyncio.run(run())


def test_no_global_user_id_field_is_introduced() -> None:
    for cls in (VerifiedWalletProof,):
        assert "global_user_id" not in {field.name for field in fields(cls)}
