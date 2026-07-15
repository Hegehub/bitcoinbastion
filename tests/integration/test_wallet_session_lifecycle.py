from __future__ import annotations

import asyncio
from tests.unit.test_wallet_session_service import _ctx, _public_key, _service
from app.services.wallet_auth.device_key_validation import compute_device_key_fingerprint

import pytest


def test_wallet_session_lifecycle_create_validate_freeze_rejects_replay():
    async def run():
        public_key = _public_key()
        fingerprint = compute_device_key_fingerprint(public_key)
        service, _events = _service()
        result = await service.create_session(auth_context=_ctx(fingerprint), session_public_key=public_key)
        context = await service.validate_session_state(session_token=result.session_token)
        assert context.requires_request_signature is True
        assert context.session_public_key_fingerprint == fingerprint
        await service.freeze_sessions_for_device(
            principal_hash=context.principal_hash,
            device_key_fingerprint=context.device_key_fingerprint,
            reason_code="device_revoked",
        )
        with pytest.raises(Exception):
            await service.validate_session_state(session_token=result.session_token)
        with pytest.raises(Exception):
            await service.create_session(auth_context=_ctx(fingerprint), session_public_key=public_key)

    asyncio.run(run())
