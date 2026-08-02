from datetime import UTC, datetime

import pytest

from app.api.access_dependencies import _validate_fresh_step_up
from tests.unit.test_wallet_lnurl_access_dependencies import context


def test_k1_is_not_withdraw_authorization_and_fresh_intent_is_required() -> None:
    with pytest.raises(Exception):
        _validate_fresh_step_up(context(metadata={"k1_verified": True}), "valuable_lnurl_withdraw", max_age_seconds=300)
    now = datetime.now(UTC)
    approved = context(
        is_step_up_verified=True,
        metadata={"step_up_evidence": {"action": "valuable_lnurl_withdraw", "intent_hash": "sha256:intent", "method": "lnurl_auth", "verified_at": now, "status": "active"}},
    )
    _validate_fresh_step_up(approved, "valuable_lnurl_withdraw", max_age_seconds=300)
