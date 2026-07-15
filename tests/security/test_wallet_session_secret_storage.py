from __future__ import annotations

import asyncio
import pytest

from app.services.wallet_auth.device_key_validation import compute_device_key_fingerprint
from app.services.wallet_auth.session_service import InMemoryWalletSessionRepository, WalletSessionError
from tests.unit.test_wallet_session_service import _ctx, _public_key, _service


def test_raw_token_private_key_and_wallet_secrets_are_not_stored_or_logged():
    async def run():
        public_key = _public_key()
        fingerprint = compute_device_key_fingerprint(public_key)
        repo = InMemoryWalletSessionRepository()
        service, events = _service(repository=repo)
        result = await service.create_session(auth_context=_ctx(fingerprint), session_public_key=public_key)
        stored = await repo.get_by_lookup_hash(result.context.session_lookup_hash)
        serialized = repr(stored) + repr(events)
        assert result.session_token not in serialized
        forbidden = ["private_key", "seed phrase", "mnemonic", "xprv", "wallet_signature", "bitcoin address"]
        assert not any(secret in serialized.lower() for secret in forbidden)
        assert stored is not None
        assert "private" not in stored.session_public_key_b64.lower()



    asyncio.run(run())
def test_session_private_key_input_is_rejected_safely():
    async def run():
        public_key = _public_key()
        fingerprint = compute_device_key_fingerprint(public_key)
        service, _events = _service()
        with pytest.raises(WalletSessionError) as exc:
            await service.create_session(
                auth_context=_ctx(fingerprint),
                session_public_key="-----BEGIN PRIVATE KEY-----\nnot-a-session-public-key",
            )
        assert "not-a-session-public-key" not in str(exc.value)

    asyncio.run(run())
