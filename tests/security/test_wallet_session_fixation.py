from __future__ import annotations

import asyncio
import pytest

from dataclasses import replace

from app.services.wallet_auth.device_key_validation import compute_device_key_fingerprint
from app.services.wallet_auth.session_service import WalletSessionError
from tests.unit.test_wallet_session_service import _ctx, _public_key, _service


def test_client_supplied_session_token_is_rejected_and_tokens_are_unique():
    async def run():
        public_key = _public_key()
        fingerprint = compute_device_key_fingerprint(public_key)
        service, _events = _service(principal_limit=10, device_limit=10)
        with pytest.raises(WalletSessionError) as exc:
            await service.create_session(
                auth_context=_ctx(fingerprint),
                session_public_key=public_key,
                client_supplied_token="sess_attacker_chosen",
            )
        assert exc.value.reason_code == "wallet_session_fixation_rejected"
        first = await service.create_session(auth_context=_ctx(fingerprint), session_public_key=public_key)
        second = await service.create_session(
            auth_context=replace(_ctx(fingerprint), challenge_id="challenge-2"),
            session_public_key=public_key,
        )
        assert first.session_token != second.session_token

    asyncio.run(run())
