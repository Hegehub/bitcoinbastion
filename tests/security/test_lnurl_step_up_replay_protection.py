from __future__ import annotations

import asyncio

import pytest

from app.services.lnurl.auth_step_up import LNURLAuthStepUpCompleteRequest, LNURLAuthStepUpConsumedError, LNURLStepUpCriticalAction
from tests.unit.test_lnurl_auth_step_up_service import callback, new_service, request


def test_step_up_authorization_is_single_use() -> None:
    svc, principal = new_service()
    challenge = asyncio.run(svc.start_step_up(request(principal.principal_hash)))
    record = svc.repository.get(challenge.step_up_id)
    assert record is not None
    result = asyncio.run(svc.complete_step_up(LNURLAuthStepUpCompleteRequest(challenge.step_up_id, "session-token", callback(record, principal), record.policy_hash, record.intent_hash, record.resource_hash, record.requested_scopes)))
    assert result.authorization and result.authorization.authorization_reference
    svc.consume_authorization(authorization_reference=result.authorization.authorization_reference, step_up_id=challenge.step_up_id, session_fingerprint="sha256:session", action=LNURLStepUpCriticalAction.CREATE_API_KEY, resource_hash=record.resource_hash, scopes=record.approved_scopes)
    with pytest.raises(LNURLAuthStepUpConsumedError):
        asyncio.run(svc.complete_step_up(LNURLAuthStepUpCompleteRequest(challenge.step_up_id, "session-token", callback(record, principal), record.policy_hash, record.intent_hash, record.resource_hash, record.requested_scopes)))
