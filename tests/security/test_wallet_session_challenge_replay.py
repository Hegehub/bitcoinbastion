from __future__ import annotations

import asyncio

from app.services.wallet_auth.device_key_validation import compute_device_key_fingerprint
from tests.unit.test_wallet_session_service import ChallengeConsumer, _ctx, _public_key, _service


def test_wallet_challenge_cannot_issue_two_sessions_through_replay():
    async def run():
        public_key = _public_key()
        fingerprint = compute_device_key_fingerprint(public_key)
        challenge = ChallengeConsumer()
        service, _events = _service(challenge=challenge, principal_limit=10, device_limit=10)
        results = await asyncio.gather(
            service.create_session(auth_context=_ctx(fingerprint), session_public_key=public_key),
            service.create_session(auth_context=_ctx(fingerprint), session_public_key=public_key),
            return_exceptions=True,
        )
        assert sum(not isinstance(result, Exception) for result in results) == 1
        assert sum(isinstance(result, Exception) for result in results) == 1

    asyncio.run(run())
