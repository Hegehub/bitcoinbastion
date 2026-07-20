from __future__ import annotations

import pytest

from app.services.lnurl.comment_allowed import (
    LNURLCommentClassification,
    LNURLCommentConfigurationError,
    LNURLCommentContext,
    LNURLCommentForbiddenCharactersError,
    LNURLCommentInvalidEncodingError,
    LNURLCommentNotAllowedError,
    LNURLCommentService,
    LNURLCommentStorageMode,
    LNURLCommentTooLongError,
)


def test_missing_comment_allowed_resolves_to_zero() -> None:
    service = LNURLCommentService()
    assert service.resolve_comment_limit(LNURLCommentContext()) == 0


def test_zero_disables_comments() -> None:
    service = LNURLCommentService()
    with pytest.raises(LNURLCommentNotAllowedError):
        service.validate_comment("hello", 0)


def test_positive_value_permits_comments() -> None:
    validated = LNURLCommentService().validate_comment("order 123", 20)
    assert validated.present is True
    assert validated.comment_hash.startswith("sha256:")
    assert validated.storage_mode == LNURLCommentStorageMode.HASH_ONLY


@pytest.mark.parametrize("value", [-1, True, 1.2, 281])
def test_invalid_comment_allowed_rejected(value) -> None:
    with pytest.raises(LNURLCommentConfigurationError):
        LNURLCommentService().validate_comment_allowed(value)  # type: ignore[arg-type]


def test_effective_limit_is_minimum_and_missing_policy_is_zero() -> None:
    service = LNURLCommentService()
    assert service.resolve_comment_limit(LNURLCommentContext(product_max_chars=200, merchant_max_chars=120, terminal_max_chars=80, request_max_chars=100)) == 80
    assert service.resolve_comment_limit(LNURLCommentContext(product_max_chars=200, merchant_max_chars=None, terminal_max_chars=80, request_max_chars=100)) == 0


def test_exact_character_boundary_accepted_and_over_boundary_rejected() -> None:
    service = LNURLCommentService()
    assert service.validate_comment("x" * 5, 5).character_count == 5
    with pytest.raises(LNURLCommentTooLongError):
        service.validate_comment("x" * 6, 5)


def test_cyrillic_emoji_and_multibyte_counts_are_deterministic() -> None:
    service = LNURLCommentService()
    assert service.validate_comment("Привет", 6).character_count == 6
    assert service.validate_comment("😀😀", 2).character_count == 2
    assert service.validate_comment("é", 1).character_count == 1


def test_normalized_unicode_hash_stable() -> None:
    service = LNURLCommentService()
    composed = service.validate_comment("é", 1)
    decomposed = service.validate_comment("e\u0301", 2)
    assert composed.normalized_comment == decomposed.normalized_comment
    assert composed.comment_hash == decomposed.comment_hash


def test_empty_and_whitespace_behavior() -> None:
    service = LNURLCommentService()
    assert service.validate_comment(None, 10).present is False
    assert service.validate_comment("", 10).present is False
    whitespace = service.validate_comment("   ", 10)
    assert whitespace.normalized_comment == ""
    assert whitespace.character_count == 0


def test_percent_decoding_exactly_once_and_double_decode_rejected() -> None:
    service = LNURLCommentService()
    assert service.validate_comment("Order%20reference%20123", 25).normalized_comment == "Order reference 123"
    with pytest.raises(LNURLCommentInvalidEncodingError):
        service.validate_comment("Order%2520reference", 25)


@pytest.mark.parametrize("comment", ["bad\x00value", "bad\r\nheader", "bad\x1fcontrol"])
def test_control_characters_rejected(comment: str) -> None:
    with pytest.raises(LNURLCommentForbiddenCharactersError):
        LNURLCommentService().validate_comment(comment, 50)


def test_comment_hash_redaction_and_no_raw_storage_by_default() -> None:
    service = LNURLCommentService()
    validated = service.validate_comment("<script>alert(1)</script>", 40)
    assert validated.comment_hash.startswith("sha256:")
    assert validated.storage_mode == LNURLCommentStorageMode.HASH_ONLY
    assert "<script>" not in service.redact_comment("<script>alert(1)</script>")
    assert "html_script_like_text" in validated.suspicious_text_flags


def test_payregister_context_classification() -> None:
    service = LNURLCommentService()
    validated = service.validate_comment("Order 123", 20, context=LNURLCommentContext(flow_type="payregister_terminal"))
    assert validated.classification == LNURLCommentClassification.MERCHANT_NOTE
