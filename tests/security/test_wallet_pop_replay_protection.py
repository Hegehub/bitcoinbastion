from __future__ import annotations

import asyncio

from app.services.wallet_auth.device_key_validation import compute_device_key_fingerprint
from app.services.wallet_auth.request_verifier import InMemoryWalletPoPNonceRegistry, WalletPoPRequestVerifier
from tests.unit.test_wallet_pop_request_verifier import BODY, NOW, PATH, QUERY, _headers, _keypair
from tests.unit.test_wallet_session_service import _ctx, _service


def test_identical_signed_request_replay_and_concurrency_are_rejected():
    async def run():
        private, public = _keypair()
        fp = compute_device_key_fingerprint(public)
        service, _ = _service(principal_limit=10, device_limit=10)
        session = await service.create_session(auth_context=_ctx(fp), session_public_key=public)
        registry = InMemoryWalletPoPNonceRegistry()
        verifier = WalletPoPRequestVerifier(session_service=service, nonce_registry=registry, clock=lambda: NOW)
        headers = _headers(session.session_token, private, session.context.session_lookup_hash)
        first = await verifier.verify_request(method="GET", path=PATH, query_string=QUERY, body=BODY, headers=headers)
        assert first.nonce_hash.startswith("hmac-sha256:")
        try:
            await verifier.verify_request(method="GET", path=PATH, query_string=QUERY, body=BODY, headers=headers)
        except Exception as exc:
            assert getattr(exc, "reason_code") == "pop_replay_detected"
        results = await asyncio.gather(
            verifier.verify_request(method="GET", path=PATH, query_string=QUERY, body=BODY, headers=_headers(session.session_token, private, session.context.session_lookup_hash, nonce="b"*22)),
            verifier.verify_request(method="GET", path=PATH, query_string=QUERY, body=BODY, headers=_headers(session.session_token, private, session.context.session_lookup_hash, nonce="b"*22)),
            return_exceptions=True,
        )
        assert sum(not isinstance(result, Exception) for result in results) == 1
        assert sum(getattr(result, "reason_code", None) == "pop_replay_detected" for result in results if isinstance(result, Exception)) == 1
    asyncio.run(run())
