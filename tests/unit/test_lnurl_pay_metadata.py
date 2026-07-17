from __future__ import annotations

import base64
import json

import pytest

from app.services.lnurl.pay_metadata import (
    IMAGE_JPEG_BASE64,
    IMAGE_PNG_BASE64,
    LNURLMetadataImage,
    LNURLPayMetadataBuilder,
    LNURLPayMetadataEntry,
    MetadataImageTooLargeError,
    MetadataValueTooLongError,
    MissingPlainTextMetadataError,
    DuplicateMetadataTypeError,
    UnsupportedMetadataTypeError,
    UnsafeMetadataContentError,
    InvalidLightningIdentifierError,
    InvalidMetadataImageError,
    TEXT_IDENTIFIER,
    TEXT_LONG_DESC,
    TEXT_PLAIN,
    metadata_result_from_json,
    validate_lightning_identifier,
)

PNG_B64 = base64.b64encode(b"\x89PNG\r\n\x1a\n" + b"\x00" * 8).decode()
JPEG_B64 = base64.b64encode(b"\xff\xd8\xff" + b"\x00" * 8).decode()
SVG_B64 = base64.b64encode(b"<svg></svg>").decode()


def test_subscription_metadata_contains_exactly_one_plain_text() -> None:
    result = LNURLPayMetadataBuilder().build_subscription_metadata(plan_code="pro_pass", duration_label="1 month")

    assert [entry.mime_type for entry in result.entries].count(TEXT_PLAIN) == 1
    assert result.plain_text == "Bitcoin Bastion Pro Pass — 1 month"


def test_missing_empty_and_duplicate_plain_text_fail() -> None:
    builder = LNURLPayMetadataBuilder()
    with pytest.raises(MissingPlainTextMetadataError):
        builder.canonicalize([LNURLPayMetadataEntry(TEXT_LONG_DESC, "desc")])
    with pytest.raises(MissingPlainTextMetadataError):
        builder.build_custom_metadata(plain_text="  ")
    with pytest.raises(DuplicateMetadataTypeError):
        builder.canonicalize([LNURLPayMetadataEntry(TEXT_PLAIN, "a"), LNURLPayMetadataEntry(TEXT_PLAIN, "b")])


def test_canonicalization_hash_order_and_unicode_are_stable() -> None:
    builder = LNURLPayMetadataBuilder()
    first = builder.canonicalize(
        [
            LNURLPayMetadataEntry(TEXT_IDENTIFIER, "Pro@Bitcoin-Bastion.com"),
            LNURLPayMetadataEntry(TEXT_PLAIN, "Bitcoin Bastion Pro Pass — 1 month"),
            LNURLPayMetadataEntry(TEXT_LONG_DESC, "Advanced signals for café operators."),
        ]
    )
    second = builder.canonicalize(
        [
            LNURLPayMetadataEntry(TEXT_LONG_DESC, "Advanced signals for café operators."),
            LNURLPayMetadataEntry(TEXT_PLAIN, "Bitcoin Bastion Pro Pass — 1 month"),
            LNURLPayMetadataEntry(TEXT_IDENTIFIER, "pro@bitcoin-bastion.com"),
        ]
    )

    assert first.canonical_json == second.canonical_json
    assert first.metadata_hash == second.metadata_hash
    assert json.loads(first.canonical_json)[0][0] == TEXT_PLAIN
    assert "café" in first.canonical_json


@pytest.mark.parametrize(
    ("plan", "display"),
    [
        ("lite_pass", "Lite"),
        ("basic_pass", "Basic"),
        ("plus_pass", "Plus"),
        ("pro_pass", "Pro"),
        ("business_pass", "Business"),
        ("enterprise_pass", "Enterprise"),
    ],
)
def test_subscription_templates_for_all_plans(plan: str, display: str) -> None:
    result = LNURLPayMetadataBuilder().build_subscription_metadata(plan_code=plan, duration_label="1 month")

    assert f"Bitcoin Bastion {display} Pass — 1 month" == result.plain_text
    assert "Base" not in result.plain_text
    assert any(entry.mime_type == TEXT_LONG_DESC for entry in result.entries)


def test_unknown_plan_fails_safely() -> None:
    with pytest.raises(Exception):
        LNURLPayMetadataBuilder().build_subscription_metadata(plan_code="base_pass", duration_label="1 month")


def test_unsupported_html_control_and_excessive_values_fail() -> None:
    builder = LNURLPayMetadataBuilder()
    with pytest.raises(UnsupportedMetadataTypeError):
        builder.canonicalize([LNURLPayMetadataEntry(TEXT_PLAIN, "safe"), LNURLPayMetadataEntry("text/html", "<b>x</b>")])
    with pytest.raises(UnsafeMetadataContentError):
        builder.build_custom_metadata(plain_text="<script>alert(1)</script>")
    with pytest.raises(UnsafeMetadataContentError):
        builder.build_custom_metadata(plain_text="hello\x00world")
    with pytest.raises(MetadataValueTooLongError):
        builder.build_custom_metadata(plain_text="x" * 257)
    with pytest.raises(MetadataValueTooLongError):
        builder.build_custom_metadata(plain_text="safe", long_description="x" * 2049)


def test_identifier_validation() -> None:
    assert validate_lightning_identifier("Store-12@PayRegister.Bitcoin-Bastion.com.") == "store-12@payregister.bitcoin-bastion.com"
    for bad in ["https://store@example.com", "store@example.com?x=1", "store@example.com#frag", "store example.com", "principal_hash@wallet.example"]:
        with pytest.raises(InvalidLightningIdentifierError):
            validate_lightning_identifier(bad)


def test_images_validated_and_ordered() -> None:
    png = LNURLPayMetadataBuilder().build_custom_metadata(plain_text="Coffee", image=LNURLMetadataImage(IMAGE_PNG_BASE64, PNG_B64))
    jpeg = LNURLPayMetadataBuilder().build_custom_metadata(plain_text="Coffee", image=LNURLMetadataImage(IMAGE_JPEG_BASE64, JPEG_B64))

    assert png.entries[-1].mime_type == IMAGE_PNG_BASE64
    assert jpeg.entries[-1].mime_type == IMAGE_JPEG_BASE64
    with pytest.raises(InvalidMetadataImageError):
        LNURLPayMetadataBuilder().build_custom_metadata(plain_text="Coffee", image=LNURLMetadataImage(IMAGE_PNG_BASE64, "not-base64"))
    with pytest.raises(InvalidMetadataImageError):
        LNURLPayMetadataBuilder().build_custom_metadata(plain_text="Coffee", image=LNURLMetadataImage(IMAGE_JPEG_BASE64, PNG_B64))
    with pytest.raises(InvalidMetadataImageError):
        LNURLPayMetadataBuilder().build_custom_metadata(plain_text="Coffee", image=LNURLMetadataImage(IMAGE_PNG_BASE64, JPEG_B64))
    with pytest.raises(InvalidMetadataImageError):
        LNURLPayMetadataBuilder().build_custom_metadata(plain_text="Coffee", image=LNURLMetadataImage(IMAGE_PNG_BASE64, SVG_B64))
    with pytest.raises(InvalidMetadataImageError):
        LNURLPayMetadataBuilder().build_custom_metadata(plain_text="Coffee", image=LNURLMetadataImage(IMAGE_PNG_BASE64, "https://example.com/logo.png"))


def test_oversized_image_rejected() -> None:
    tiny_limit = LNURLPayMetadataBuilder(max_image_bytes=4)
    with pytest.raises(MetadataImageTooLargeError):
        tiny_limit.build_custom_metadata(plain_text="Coffee", image=LNURLMetadataImage(IMAGE_PNG_BASE64, PNG_B64))


def test_payregister_metadata_uses_public_references_without_customer_or_cashier_identity() -> None:
    result = LNURLPayMetadataBuilder().build_payregister_metadata(
        merchant_display_name="Example Coffee",
        order_reference="9231",
        terminal_reference="  Store 12 Terminal 3  ",
        description="Latte and croissant",
        lightning_identifier="store-12@payregister.bitcoin-bastion.com",
    )

    assert result.plain_text == "Payment to Example Coffee — Order 9231"
    assert "Store 12 Terminal 3" in result.canonical_json
    assert "customer" not in result.canonical_json.lower()
    assert "cashier" not in result.canonical_json.lower()
    with pytest.raises(UnsafeMetadataContentError):
        LNURLPayMetadataBuilder().build_payregister_metadata(
            merchant_display_name="Example Coffee",
            order_reference="db:123",
            terminal_reference=None,
            description=None,
        )


def test_metadata_hash_changes_on_payment_context_changes() -> None:
    builder = LNURLPayMetadataBuilder()
    first = builder.build_custom_metadata(plain_text="Pay invoice A", identifier="a@example.com")
    text_changed = builder.build_custom_metadata(plain_text="Pay invoice B", identifier="a@example.com")
    identifier_changed = builder.build_custom_metadata(plain_text="Pay invoice A", identifier="b@example.com")
    image_changed = builder.build_custom_metadata(plain_text="Pay invoice A", identifier="a@example.com", image=LNURLMetadataImage(IMAGE_PNG_BASE64, PNG_B64))

    assert first.metadata_hash.startswith("sha256:")
    assert first.metadata_hash != str(hash(first.canonical_json))
    assert first.metadata_hash != text_changed.metadata_hash
    assert first.metadata_hash != identifier_changed.metadata_hash
    assert first.metadata_hash != image_changed.metadata_hash


def test_metadata_result_from_json_validates_and_canonicalizes() -> None:
    result = metadata_result_from_json('[["text/identifier","pro@bitcoin-bastion.com"],["text/plain","Pro"]]')

    assert result.canonical_json == '[["text/plain","Pro"],["text/identifier","pro@bitcoin-bastion.com"]]'
