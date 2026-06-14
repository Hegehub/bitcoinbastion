from app.services.events.webhook_signature import build_signed_payload, verify_signature


def signed_headers(raw_body: str = '{"ok":true}') -> dict[str, str]:
    return build_signed_payload(
        secret="whsec_test",
        event_type="signal.published",
        delivery_id="whd_test",
        timestamp=2000,
        raw_body=raw_body,
    )


def test_signature_covers_timestamp_delivery_event_and_body() -> None:
    raw_body = '{"ok":true}'
    headers = signed_headers(raw_body)

    assert verify_signature(
        secret="whsec_test",
        signature_header=headers["X-Bastion-Signature"],
        timestamp=2000,
        delivery_id="whd_test",
        event_type="signal.published",
        raw_body=raw_body,
        now=2000,
    )
    assert not verify_signature(
        secret="whsec_test",
        signature_header=headers["X-Bastion-Signature"],
        timestamp=2000,
        delivery_id="whd_other",
        event_type="signal.published",
        raw_body=raw_body,
        now=2000,
    )
    assert not verify_signature(
        secret="whsec_test",
        signature_header=headers["X-Bastion-Signature"],
        timestamp=2000,
        delivery_id="whd_test",
        event_type="trace.report.created",
        raw_body=raw_body,
        now=2000,
    )


def test_stale_missing_and_malformed_signatures_are_rejected() -> None:
    raw_body = "{}"
    headers = signed_headers(raw_body)

    assert not verify_signature(
        secret="whsec_test",
        signature_header=headers["X-Bastion-Signature"],
        timestamp=1000,
        delivery_id="whd_test",
        event_type="signal.published",
        raw_body=raw_body,
        now=2000,
    )
    assert not verify_signature(
        secret="whsec_test",
        signature_header=headers["X-Bastion-Signature"],
        timestamp=2000,
        delivery_id=None,
        event_type="signal.published",
        raw_body=raw_body,
        now=2000,
    )
    assert not verify_signature(
        secret="whsec_test",
        signature_header="not-a-signature",
        timestamp=2000,
        delivery_id="whd_test",
        event_type="signal.published",
        raw_body=raw_body,
        now=2000,
    )
