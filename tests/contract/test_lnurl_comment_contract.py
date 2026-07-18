from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.schemas.lnurl import LNURLPayCallbackRequest, LNURLPayRequestResponse, LNURLValidatedCommentMetadata


def test_comment_allowed_is_numeric_and_omitted_when_disabled() -> None:
    response = LNURLPayRequestResponse(tag="payRequest", callback="https://pay.example.com/cb", min_sendable=1, max_sendable=1, metadata="[]", comment_allowed=120)
    payload = response.model_dump(by_alias=True)
    assert isinstance(payload["comment_allowed"], int)
    no_comment = LNURLPayRequestResponse(tag="payRequest", callback="https://pay.example.com/cb", min_sendable=1, max_sendable=1, metadata="[]")
    assert no_comment.comment_allowed is None


@pytest.mark.parametrize("bad", [True, 1.5, -1])
def test_comment_allowed_rejects_bool_float_negative(bad) -> None:
    with pytest.raises(ValidationError):
        LNURLPayRequestResponse(tag="payRequest", callback="https://pay.example.com/cb", min_sendable=1, max_sendable=1, metadata="[]", comment_allowed=bad)


def test_callback_accepts_optional_comment_as_untrusted_metadata() -> None:
    request = LNURLPayCallbackRequest(payment_id="lpay", amount=1000, comment="Order reference 123")
    assert request.comment == "Order reference 123"
    assert "cannot authorize" in LNURLPayCallbackRequest.model_fields["comment"].description


def test_validated_comment_metadata_schema_is_hash_only_safe() -> None:
    metadata = LNURLValidatedCommentMetadata(
        present=True,
        normalized_comment="raw hidden internally",
        comment_hash="sha256:abc",
        character_count=12,
        allowed_character_count=120,
        storage_mode="hash_only",
        classification="merchant_note",
    )
    dumped = metadata.model_dump()
    assert "normalized_comment" not in dumped
    assert dumped["comment_hash"] == "sha256:abc"


def test_protocol_error_shape_is_safe() -> None:
    error = {"status": "ERROR", "reason": "Comment exceeds the allowed length."}
    assert set(error) == {"status", "reason"}
    assert "sha256:" not in str(error)
    assert "raw comment" not in str(error).lower()
