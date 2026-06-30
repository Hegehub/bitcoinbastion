import inspect

from app.services.events import webhook_signature as signature_module
from app.services.events.webhook_signature import (
    build_signed_payload,
    verify_signature,
    webhook_signature,
)


def test_signature_generation_is_deterministic_for_fixed_input() -> None:
    signature = webhook_signature(
        secret="whsec_test_secret",
        timestamp=1780000000,
        raw_body='{"event_type":"signal.published"}',
    )

    assert signature == ("v1=2333c244f651a34b4fca8c55df09beef3acb01e1f6fa4fa0cd3139fb57ca16ba")


def test_valid_signature_verifies_and_wrong_secret_fails() -> None:
    raw_body = '{"data":{"safe":true}}'
    headers = build_signed_payload(
        secret="whsec_test_secret",
        event_type="webhook.test",
        delivery_id="whd_test",
        timestamp=1780000000,
        raw_body=raw_body,
    )

    assert verify_signature(
        secret="whsec_test_secret",
        signature_header=headers["X-Bastion-Signature"],
        timestamp=1780000000,
        delivery_id="whd_test",
        event_type="webhook.test",
        raw_body=raw_body,
        now=1780000000,
    )
    assert not verify_signature(
        secret="whsec_wrong",
        signature_header=headers["X-Bastion-Signature"],
        timestamp=1780000000,
        delivery_id="whd_test",
        event_type="webhook.test",
        raw_body=raw_body,
        now=1780000000,
    )


def test_replay_tolerance_and_signature_prefix_are_enforced() -> None:
    raw_body = "{}"
    signature = webhook_signature(secret="whsec_test_secret", timestamp=100, raw_body=raw_body)

    assert not verify_signature(
        secret="whsec_test_secret",
        signature_header=signature,
        timestamp=100,
        delivery_id="whd_test",
        event_type="webhook.test",
        raw_body=raw_body,
        now=500,
    )
    assert not verify_signature(
        secret="whsec_test_secret",
        signature_header=signature,
        timestamp=1000,
        delivery_id="whd_test",
        event_type="webhook.test",
        raw_body=raw_body,
        now=500,
    )
    assert not verify_signature(
        secret="whsec_test_secret",
        signature_header=signature.replace("v1=", "v2="),
        timestamp=100,
        delivery_id="whd_test",
        event_type="webhook.test",
        raw_body=raw_body,
        now=100,
    )


def test_verification_uses_constant_time_compare() -> None:
    source = inspect.getsource(signature_module.verify_signature)
    assert "hmac.compare_digest" in source
