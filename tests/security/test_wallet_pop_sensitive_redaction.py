from __future__ import annotations

import asyncio

from app.services.wallet_auth.device_key_validation import compute_device_key_fingerprint
from app.services.wallet_auth.request_verifier import InMemoryWalletPoPNonceRegistry, WalletPoPRequestVerifier
from tests.unit.test_wallet_pop_request_verifier import BODY, NOW, PATH, QUERY, _headers, _keypair
from tests.unit.test_wallet_session_service import _ctx, _service


def test_pop_audit_payloads_do_not_expose_tokens_nonces_or_signatures():
    async def run():
        private, public = _keypair()
        fp = compute_device_key_fingerprint(public)
        service, _ = _service()
        session = await service.create_session(auth_context=_ctx(fp), session_public_key=public)
        events = []
        verifier = WalletPoPRequestVerifier(session_service=service, nonce_registry=InMemoryWalletPoPNonceRegistry(), clock=lambda: NOW, audit_emitter=lambda e, p: events.append((e, p)))
        headers = _headers(session.session_token, private, session.context.session_lookup_hash)
        await verifier.verify_request(method="GET", path=PATH, query_string=QUERY, body=BODY, headers=headers)
        serialized = repr(events)
        assert session.session_token not in serialized
        assert headers["Bastion-Request-Nonce"] not in serialized
        assert headers["Bastion-Request-Signature"] not in serialized
        assert "private_key" not in serialized and "mnemonic" not in serialized and "xprv" not in serialized
    asyncio.run(run())
