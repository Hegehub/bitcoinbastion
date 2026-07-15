from __future__ import annotations

import asyncio

import pytest

from app.services.wallet_auth.device_key_validation import compute_device_key_fingerprint
from app.services.wallet_auth.request_verifier import InMemoryWalletPoPNonceRegistry, WalletPoPError, WalletPoPRequestVerifier
from tests.unit.test_wallet_pop_request_verifier import BODY, NOW, PATH, QUERY, _headers, _keypair
from tests.unit.test_wallet_session_service import _ctx, _service


def test_wallet_pop_protected_request_flow_policy_boundary_and_revocation():
    async def run():
        private, public = _keypair()
        fp = compute_device_key_fingerprint(public)
        service, _events = _service(principal_limit=10, device_limit=10)
        session = await service.create_session(auth_context=_ctx(fp), session_public_key=public)
        verifier = WalletPoPRequestVerifier(session_service=service, nonce_registry=InMemoryWalletPoPNonceRegistry(), clock=lambda: NOW)
        headers = _headers(session.session_token, private, session.context.session_lookup_hash)
        verified = await verifier.verify_request(method="GET", path=PATH, query_string=QUERY, body=BODY, headers=headers)
        assert verified.requires_policy_decision is True
        assert verified.scopes == ("read",)
        with pytest.raises(WalletPoPError):
            await verifier.verify_request(method="GET", path=PATH, query_string=QUERY, body=BODY, headers=headers)
        await service.revoke_session(session_token=session.session_token, reason_code="test_revoke")
        headers2 = _headers(session.session_token, private, session.context.session_lookup_hash, nonce="d"*22)
        with pytest.raises(Exception):
            await verifier.verify_request(method="GET", path=PATH, query_string=QUERY, body=BODY, headers=headers2)
    asyncio.run(run())
