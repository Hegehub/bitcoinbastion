from __future__ import annotations

import asyncio

import pytest

from app.services.wallet_auth.device_key_validation import compute_device_key_fingerprint
from app.services.wallet_auth.request_verifier import InMemoryWalletPoPNonceRegistry, WalletPoPError, WalletPoPRequestVerifier
from tests.unit.test_wallet_pop_request_verifier import BODY, NOW, PATH, QUERY, _headers, _keypair
from tests.unit.test_wallet_session_service import _ctx, _service


def test_modified_body_json_whitespace_and_path_are_rejected():
    async def run():
        private, public = _keypair()
        fp = compute_device_key_fingerprint(public)
        service, _ = _service(principal_limit=10, device_limit=10)
        session = await service.create_session(auth_context=_ctx(fp), session_public_key=public)
        verifier = WalletPoPRequestVerifier(session_service=service, nonce_registry=InMemoryWalletPoPNonceRegistry(), clock=lambda: NOW)
        headers = _headers(session.session_token, private, session.context.session_lookup_hash, body=BODY)
        with pytest.raises(WalletPoPError) as exc:
            await verifier.verify_request(method="GET", path=PATH, query_string=QUERY, body=b'{"hello": "world"}', headers=headers)
        assert exc.value.reason_code == "pop_body_hash_mismatch"
        headers2 = _headers(session.session_token, private, session.context.session_lookup_hash, nonce="c"*22)
        with pytest.raises(WalletPoPError) as exc:
            await verifier.verify_request(method="GET", path="/api/v1/other", query_string=QUERY, body=BODY, headers=headers2)
        assert exc.value.reason_code == "invalid_pop_signature"
    asyncio.run(run())
