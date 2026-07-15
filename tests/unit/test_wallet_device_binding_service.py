from __future__ import annotations

import asyncio
from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from app.db.repositories.wallet_device_repository import InMemoryWalletDeviceRepository
from app.domain.wallet_auth.devices import WalletDeviceBindingMethod, WalletDeviceClass, WalletDeviceStatus
from app.domain.wallet_auth.networks import WalletNetwork
from app.domain.wallet_auth.principals import WalletPrincipalStatus
from app.domain.wallet_auth.proofs import WalletProofType, WalletVerificationStrength
from app.services.wallet_auth.device_binding_service import (
    DeviceBindingActionMismatchError,
    DeviceBindingProofExpiredError,
    DeviceBindingProofRequiredError,
    DeviceBindingService,
    DeviceBindingTooWeakError,
    DeviceKeyRotationNotAllowedError,
    DeviceLimitExceededError,
    DeviceNotActiveError,
    VerifiedPrincipalProofContext,
)
from app.services.wallet_auth.device_key_validation import validate_device_public_key
from app.services.wallet_auth.principal_types import PrincipalType, WalletPrincipalRecord
from app.services.wallet_auth.privacy_commitments import compute_hmac_lookup_hash, compute_sha256_commitment


class FakePrincipalLookup:
    def __init__(self, record: WalletPrincipalRecord) -> None:
        self.record = record

    async def get_principal(self, principal_hash: str) -> WalletPrincipalRecord:
        if principal_hash != self.record.principal_hash:
            raise KeyError("wallet_principal_not_found")
        return self.record

    async def verify_principal_status(self, principal_hash: str) -> WalletPrincipalRecord:
        record = await self.get_principal(principal_hash)
        if record.status is not WalletPrincipalStatus.ACTIVE:
            raise DeviceNotActiveError(f"principal_{record.status.value}")
        return record


class FakeRevocationChecker:
    def __init__(self) -> None:
        self.revoked: set[tuple[str, str]] = set()

    def is_revoked(self, *, target_type: str, target_hash: str) -> bool:
        return (target_type, target_hash) in self.revoked


def _public_key_bytes() -> bytes:
    return Ed25519PrivateKey.generate().public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )


def _principal(*, principal_type: PrincipalType = PrincipalType.BITCOIN_WALLET_PRINCIPAL) -> WalletPrincipalRecord:
    now = datetime.now(UTC)
    return WalletPrincipalRecord(
        principal_hash=compute_hmac_lookup_hash("test-pepper", "principal", principal_type.value),
        principal_type=principal_type,
        status=WalletPrincipalStatus.ACTIVE,
        network=WalletNetwork.BITCOIN_MAINNET,
        primary_proof_method=WalletProofType.BIP322,
        current_proof_strength=WalletVerificationStrength.STANDARD,
        highest_verified_strength=WalletVerificationStrength.STANDARD,
        address_hash=compute_hmac_lookup_hash("test-pepper", "address", "wallet"),
        script_pubkey_hash=compute_sha256_commitment("script"),
        schema_epoch=1,
        crypto_epoch=1,
        policy_epoch=1,
        created_at=now,
        updated_at=now,
        last_verified_at=now,
    )


def _context(
    principal: WalletPrincipalRecord,
    *,
    proof_type: WalletProofType = WalletProofType.BIP322,
    strength: WalletVerificationStrength = WalletVerificationStrength.STANDARD,
    action: str = "register",
    expected_fingerprint: str | None = None,
    expires_delta: timedelta = timedelta(minutes=5),
) -> VerifiedPrincipalProofContext:
    now = datetime.now(UTC)
    return VerifiedPrincipalProofContext(
        principal_hash=principal.principal_hash,
        principal_type=principal.principal_type,
        proof_type=proof_type,
        verification_strength=strength,
        proof_fingerprint=compute_sha256_commitment(f"proof-{action}"),
        challenge_id_hash=compute_sha256_commitment(f"challenge-{action}"),
        intent_hash=compute_sha256_commitment(f"intent-{action}"),
        action=action,
        network=principal.network,
        auth_domain="auth.example.test" if proof_type is WalletProofType.LNURL_AUTH else None,
        verified_at=now,
        expires_at=now + expires_delta,
        policy_hash=compute_sha256_commitment("policy"),
        verifier_name="test-verifier",
        verifier_version="1",
        expected_device_key_fingerprint=expected_fingerprint,
    )


def _service(
    principal: WalletPrincipalRecord,
    *,
    events: list[tuple[str, dict[str, object]]] | None = None,
    revocation: FakeRevocationChecker | None = None,
    repository: InMemoryWalletDeviceRepository | None = None,
) -> DeviceBindingService:
    publisher = (lambda event, payload: events.append((event, payload))) if events is not None else None
    return DeviceBindingService(
        repository=repository,
        principal_lookup=FakePrincipalLookup(principal),
        server_pepper="device-test-pepper",
        event_publisher=publisher,
        revocation_checker=revocation,
    )


def test_valid_bip322_registration_proof_binds_initial_device() -> None:
    async def run() -> None:
        principal = _principal()
        key = _public_key_bytes()
        record = await _service(principal).register_initial_device(
            proof_context=_context(principal),
            device_public_key=key,
            device_class=WalletDeviceClass.DESKTOP_VAULT,
        )
        assert record.status is WalletDeviceStatus.ACTIVE
        assert record.binding_method is WalletDeviceBindingMethod.WALLET_PROOF_REGISTRATION
        assert record.proof_type is WalletProofType.BIP322

    asyncio.run(run())


def test_valid_lnurl_auth_register_proof_binds_initial_device() -> None:
    async def run() -> None:
        principal = _principal(principal_type=PrincipalType.LIGHTNING_WALLET_PRINCIPAL)
        record = await _service(principal).register_initial_device(
            proof_context=_context(principal, proof_type=WalletProofType.LNURL_AUTH),
            device_public_key=_public_key_bytes(),
            device_class=WalletDeviceClass.MOBILE_VAULT,
        )
        assert record.binding_method is WalletDeviceBindingMethod.LNURL_AUTH_REGISTRATION
        assert record.auth_domain == "auth.example.test"

    asyncio.run(run())


def test_expired_proof_context_fails() -> None:
    async def run() -> None:
        principal = _principal()
        with pytest.raises(DeviceBindingProofExpiredError):
            await _service(principal).register_initial_device(
                proof_context=_context(principal, expires_delta=timedelta(seconds=-1)),
                device_public_key=_public_key_bytes(),
            )

    asyncio.run(run())


def test_principal_mismatch_fails() -> None:
    async def run() -> None:
        principal = _principal()
        other = replace(principal, principal_hash=compute_hmac_lookup_hash("test-pepper", "principal", "other"))
        with pytest.raises(KeyError):
            await _service(principal).register_initial_device(
                proof_context=_context(other),
                device_public_key=_public_key_bytes(),
            )

    asyncio.run(run())


def test_revoked_principal_fails() -> None:
    async def run() -> None:
        principal = replace(_principal(), status=WalletPrincipalStatus.REVOKED)
        with pytest.raises(DeviceNotActiveError):
            await _service(principal).register_initial_device(
                proof_context=_context(principal),
                device_public_key=_public_key_bytes(),
            )

    asyncio.run(run())


def test_private_key_input_fails() -> None:
    async def run() -> None:
        principal = _principal()
        private_pem = Ed25519PrivateKey.generate().private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode("ascii")
        with pytest.raises(Exception) as exc:
            await _service(principal).register_initial_device(
                proof_context=_context(principal),
                device_public_key=private_pem,
            )
        assert private_pem not in str(exc.value)

    asyncio.run(run())


def test_duplicate_request_is_idempotent() -> None:
    async def run() -> None:
        principal = _principal()
        service = _service(principal)
        key = _public_key_bytes()
        first = await service.register_initial_device(proof_context=_context(principal), device_public_key=key)
        second = await service.register_initial_device(proof_context=_context(principal), device_public_key=key)
        assert first.id == second.id

    asyncio.run(run())


def test_fresh_bip322_device_add_proof_succeeds() -> None:
    async def run() -> None:
        principal = _principal()
        record = await _service(principal).bind_new_device(
            proof_context=_context(principal, action="device_add"),
            device_public_key=_public_key_bytes(),
            device_class=WalletDeviceClass.CLI_VAULT,
        )
        assert record.binding_method is WalletDeviceBindingMethod.WALLET_PROOF_NEW_DEVICE

    asyncio.run(run())


def test_fresh_lnurl_auth_action_auth_device_add_succeeds() -> None:
    async def run() -> None:
        principal = _principal(principal_type=PrincipalType.LIGHTNING_WALLET_PRINCIPAL)
        record = await _service(principal).bind_new_device(
            proof_context=_context(principal, proof_type=WalletProofType.LNURL_AUTH, action="auth"),
            device_public_key=_public_key_bytes(),
        )
        assert record.binding_method is WalletDeviceBindingMethod.LNURL_AUTH_NEW_DEVICE

    asyncio.run(run())


def test_lnurl_login_without_device_add_intent_fails() -> None:
    async def run() -> None:
        principal = _principal(principal_type=PrincipalType.LIGHTNING_WALLET_PRINCIPAL)
        with pytest.raises(DeviceBindingActionMismatchError):
            await _service(principal).bind_new_device(
                proof_context=_context(principal, proof_type=WalletProofType.LNURL_AUTH, action="login"),
                device_public_key=_public_key_bytes(),
            )

    asyncio.run(run())


def test_reused_proof_reference_fails_when_checker_available() -> None:
    async def run() -> None:
        principal = _principal()
        context = _context(principal, action="device_add")
        revocation = FakeRevocationChecker()
        revocation.revoked.add(("wallet_proof", context.proof_fingerprint))
        with pytest.raises(DeviceBindingProofRequiredError):
            await _service(principal, revocation=revocation).bind_new_device(
                proof_context=context,
                device_public_key=_public_key_bytes(),
            )

    asyncio.run(run())


def test_stale_proof_fails() -> None:
    async def run() -> None:
        principal = _principal()
        with pytest.raises(DeviceBindingProofExpiredError):
            await _service(principal).bind_new_device(
                proof_context=_context(principal, action="device_add", expires_delta=timedelta(seconds=-5)),
                device_public_key=_public_key_bytes(),
            )

    asyncio.run(run())


def test_compatibility_proof_cannot_enroll_high_assurance_or_payregister_device() -> None:
    async def run() -> None:
        principal = _principal()
        context = _context(
            principal,
            action="device_add",
            proof_type=WalletProofType.LEGACY_MESSAGE_SIGNATURE,
            strength=WalletVerificationStrength.COMPATIBILITY,
        )
        with pytest.raises(DeviceBindingTooWeakError):
            await _service(principal).bind_new_device(
                proof_context=context,
                device_public_key=_public_key_bytes(),
                device_class=WalletDeviceClass.HARDWARE_WALLET,
            )
        with pytest.raises(DeviceBindingTooWeakError):
            await _service(principal).bind_new_device(
                proof_context=context,
                device_public_key=_public_key_bytes(),
                device_class=WalletDeviceClass.PAYREGISTER_DEVICE,
            )

    asyncio.run(run())


def test_device_limit_exceeded_returns_structured_failure() -> None:
    async def run() -> None:
        principal = _principal()
        service = _service(principal)
        await service.register_initial_device(proof_context=_context(principal), device_public_key=_public_key_bytes())
        with pytest.raises(DeviceLimitExceededError):
            await service.bind_new_device(
                proof_context=_context(principal, action="device_add"),
                device_public_key=_public_key_bytes(),
                max_devices=1,
            )

    asyncio.run(run())


def test_concurrent_duplicate_requests_create_one_device() -> None:
    async def run() -> None:
        principal = _principal()
        service = _service(principal)
        key = _public_key_bytes()
        context = _context(principal, action="device_add")
        records = await asyncio.gather(
            service.bind_new_device(proof_context=context, device_public_key=key),
            service.bind_new_device(proof_context=context, device_public_key=key),
        )
        assert records[0].id == records[1].id

    asyncio.run(run())


def test_suspended_and_revoked_device_status_behavior() -> None:
    async def run() -> None:
        principal = _principal()
        service = _service(principal)
        key = _public_key_bytes()
        record = await service.register_initial_device(proof_context=_context(principal), device_public_key=key)
        await service.suspend_device(
            principal_hash=principal.principal_hash,
            device_key_fingerprint=record.device_key_fingerprint,
            reason_code="operator_hold",
        )
        with pytest.raises(DeviceNotActiveError):
            await service.assert_device_active(
                principal_hash=principal.principal_hash,
                device_key_fingerprint=record.device_key_fingerprint,
            )
        revoked = await service.revoke_device(
            principal_hash=principal.principal_hash,
            device_key_fingerprint=record.device_key_fingerprint,
            reason_code="compromised",
        )
        with pytest.raises(DeviceNotActiveError):
            await service.reactivate_device(
                principal_hash=principal.principal_hash,
                device_key_fingerprint=revoked.device_key_fingerprint,
                proof_context=_context(principal, action="step_up"),
            )
        activity = await service.record_device_activity(
            principal_hash=principal.principal_hash,
            device_key_fingerprint=revoked.device_key_fingerprint,
        )
        assert activity.status is WalletDeviceStatus.REVOKED

    asyncio.run(run())


def test_revocation_publishes_event() -> None:
    async def run() -> None:
        events: list[tuple[str, dict[str, object]]] = []
        principal = _principal()
        service = _service(principal, events=events)
        record = await service.register_initial_device(proof_context=_context(principal), device_public_key=_public_key_bytes())
        await service.revoke_device(
            principal_hash=principal.principal_hash,
            device_key_fingerprint=record.device_key_fingerprint,
            reason_code="compromised",
        )
        assert any(event == "wallet_device_revoked" for event, _ in events)

    asyncio.run(run())


def test_valid_rotation_context_succeeds_and_preserves_history() -> None:
    async def run() -> None:
        principal = _principal()
        service = _service(principal)
        old = await service.register_initial_device(proof_context=_context(principal), device_public_key=_public_key_bytes())
        rotated = await service.rotate_device_key(
            principal_hash=principal.principal_hash,
            old_device_key_fingerprint=old.device_key_fingerprint,
            new_device_public_key=_public_key_bytes(),
            proof_context=_context(principal, action="device_key_rotate"),
        )
        assert rotated.device_key_fingerprint != old.device_key_fingerprint
        assert old.device_key_fingerprint in rotated.metadata["previous_key_fingerprints"]

    asyncio.run(run())


def test_revoked_fingerprint_cannot_be_reused_for_rotation() -> None:
    async def run() -> None:
        principal = _principal()
        key = _public_key_bytes()
        fingerprint = validate_device_public_key(key).fingerprint
        revocation = FakeRevocationChecker()
        revocation.revoked.add(("wallet_device_key", fingerprint))
        service = _service(principal, revocation=revocation)
        old = await service.register_initial_device(proof_context=_context(principal), device_public_key=_public_key_bytes())
        with pytest.raises(DeviceKeyRotationNotAllowedError):
            await service.rotate_device_key(
                principal_hash=principal.principal_hash,
                old_device_key_fingerprint=old.device_key_fingerprint,
                new_device_public_key=key,
                proof_context=_context(principal, action="device_key_rotate"),
            )

    asyncio.run(run())


def test_rotation_without_step_up_or_proof_fails() -> None:
    async def run() -> None:
        principal = _principal()
        service = _service(principal)
        old = await service.register_initial_device(proof_context=_context(principal), device_public_key=_public_key_bytes())
        with pytest.raises(DeviceKeyRotationNotAllowedError):
            await service.rotate_device_key(
                principal_hash=principal.principal_hash,
                old_device_key_fingerprint=old.device_key_fingerprint,
                new_device_public_key=_public_key_bytes(),
                proof_context=_context(principal, action="login"),
            )

    asyncio.run(run())


def test_privacy_events_and_records_contain_hashes_only() -> None:
    async def run() -> None:
        events: list[tuple[str, dict[str, object]]] = []
        principal = _principal()
        raw_private = "-----BEGIN PRIVATE KEY-----secret-----END PRIVATE KEY-----"
        service = _service(principal, events=events)
        record = await service.register_initial_device(
            proof_context=_context(principal),
            device_public_key=_public_key_bytes(),
            client_name="Test Client",
        )
        rendered = f"{record!r} {events!r}".lower()
        assert "bc1" not in rendered
        assert "lnurl" not in rendered
        assert "raw_signature" not in rendered
        assert raw_private.lower() not in rendered
        assert "device_public_key_b64" not in events[0][1]

    asyncio.run(run())
