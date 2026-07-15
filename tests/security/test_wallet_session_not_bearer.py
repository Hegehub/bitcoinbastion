from __future__ import annotations

import asyncio
from app.services.wallet_auth.device_key_validation import compute_device_key_fingerprint
from app.services.wallet_auth.session_service import sessions_require_request_signature
from tests.unit.test_wallet_session_service import _ctx, _public_key, _service


def test_session_token_alone_is_not_bearer_authorization():
    async def run():
        public_key = _public_key()
        fingerprint = compute_device_key_fingerprint(public_key)
        service, _events = _service()
        result = await service.create_session(auth_context=_ctx(fingerprint), session_public_key=public_key)
        assert result.token_type == "PoP"
        assert result.requires_request_signature is True
        assert sessions_require_request_signature(result.context) is True
        assert "bearer" not in result.token_type.lower()
        assert not hasattr(service, "authorize_bearer")
        assert "Proof-of-Possession" in result.warning

    asyncio.run(run())
