from __future__ import annotations

import asyncio

import pytest

from tests.unit.test_lnurl_auth_step_up_service import KEY, callback, new_service, request
from app.services.lnurl.auth_step_up import LNURLAuthStepUpCompleteRequest


def test_step_up_audit_and_repr_do_not_leak_secrets() -> None:
    events = []
    svc, principal = new_service(events=events)
    challenge = asyncio.run(svc.start_step_up(request(principal.principal_hash)))
    record = svc.repository.get(challenge.step_up_id)
    assert record is not None
    result = asyncio.run(svc.complete_step_up(LNURLAuthStepUpCompleteRequest(challenge.step_up_id, "session-token", callback(record, principal), record.policy_hash, record.intent_hash, record.resource_hash, record.requested_scopes)))
    rendered = repr(events) + repr(challenge) + repr(result)
    assert KEY not in rendered
    assert "session-token" not in rendered
    assert "private_key" not in rendered.lower()
    assert "mnemonic" not in rendered.lower()
    assert "raw k1" not in rendered.lower()


def test_seed_private_key_metadata_is_rejected() -> None:
    svc, principal = new_service()
    with pytest.raises(Exception):
        asyncio.run(svc.start_step_up(request(principal.principal_hash, intent_metadata={"private_key": "secret"})))
