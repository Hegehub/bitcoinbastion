from __future__ import annotations

import asyncio

import pytest

from app.services.lnurl.auth_step_up import LNURLAuthStepUpCompleteRequest, LNURLAuthStepUpMismatchError, LNURLAuthStepUpPolicyError, LNURLStepUpCriticalAction
from tests.unit.test_lnurl_auth_step_up_service import callback, new_service, request


def test_intent_policy_resource_and_scope_tampering_are_rejected() -> None:
    svc, principal = new_service()
    challenge = asyncio.run(svc.start_step_up(request(principal.principal_hash, action=LNURLStepUpCriticalAction.PAYOUT_APPROVE)))
    record = svc.repository.get(challenge.step_up_id)
    assert record is not None
    for kwargs in (
        {"policy_hash": "sha256:tampered"},
        {"intent_hash": "sha256:tampered"},
        {"resource_hash": "sha256:other"},
        {"requested_scopes": ("api_key:create",)},
    ):
        data = {"policy_hash": record.policy_hash, "intent_hash": record.intent_hash, "resource_hash": record.resource_hash, "requested_scopes": record.requested_scopes}
        data.update(kwargs)
        with pytest.raises(LNURLAuthStepUpMismatchError):
            asyncio.run(svc.complete_step_up(LNURLAuthStepUpCompleteRequest(challenge.step_up_id, "session-token", callback(record, principal), **data)))


def test_unknown_or_wildcard_action_scope_fails_closed() -> None:
    svc, principal = new_service()
    with pytest.raises(LNURLAuthStepUpPolicyError):
        asyncio.run(svc.start_step_up(request(principal.principal_hash, requested_scopes=("admin:all",))))
