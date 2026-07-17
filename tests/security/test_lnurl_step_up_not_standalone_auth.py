from __future__ import annotations

import asyncio
from datetime import timedelta

import pytest

from app.services.lnurl.auth_step_up import ActivePoPSessionContext, LNURLAuthStepUpSessionError
from tests.unit.test_lnurl_auth_step_up_service import NOW, new_service, request


def test_lnurl_auth_proof_alone_requires_active_pop_session() -> None:
    svc, principal = new_service(
        session=ActivePoPSessionContext("session-token", "sha256:session", "hmac-sha256:other", "sha256:device", "active", NOW + timedelta(minutes=5), (), "auth.bitcoin-bastion.com")
    )
    with pytest.raises(Exception):
        asyncio.run(svc.start_step_up(request(principal.principal_hash)))


def test_expired_or_revoked_session_cannot_start_step_up() -> None:
    svc, principal = new_service(
        session=ActivePoPSessionContext("session-token", "sha256:session", principal_hash="hmac-sha256:placeholder", device_key_fingerprint="sha256:device", status="revoked", expires_at=NOW - timedelta(seconds=1), approved_scopes=(), auth_domain="auth.bitcoin-bastion.com")
    )
    with pytest.raises(LNURLAuthStepUpSessionError):
        asyncio.run(svc.start_step_up(request(principal.principal_hash)))
