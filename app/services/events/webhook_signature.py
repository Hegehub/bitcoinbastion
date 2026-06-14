from __future__ import annotations

import hashlib
import hmac
import time

BASTION_WEBHOOK_SOURCE = "bitcoin-bastion"
SIGNATURE_PREFIX = "v1="
DEFAULT_TOLERANCE_SECONDS = 300


def webhook_signature(
    *,
    secret: str,
    timestamp: int,
    raw_body: str,
    event_type: str | None = None,
    delivery_id: str | None = None,
) -> str:
    """Return the canonical v1 HMAC SHA256 signature for a webhook body.

    New deliveries bind the timestamp, delivery id, event type, and raw body.
    Older call sites without event/delivery context retain legacy signing for
    deterministic compatibility but verification requires replay fields.
    """
    if event_type is not None and delivery_id is not None:
        message = f"{timestamp}.{delivery_id}.{event_type}.{raw_body}".encode("utf-8")
    else:
        message = f"{timestamp}.{raw_body}".encode("utf-8")
    digest = hmac.new(secret.encode("utf-8"), message, hashlib.sha256).hexdigest()
    return f"{SIGNATURE_PREFIX}{digest}"


def build_signed_payload(
    *,
    secret: str,
    event_type: str,
    delivery_id: str,
    timestamp: int,
    raw_body: str,
    payload_version: int = 1,
    event_id: str | None = None,
) -> dict[str, str]:
    """Build canonical Bitcoin Bastion webhook headers without exposing the secret."""
    headers = {
        "X-Bastion-Event": event_type,
        "X-Bastion-Timestamp": str(timestamp),
        "X-Bastion-Delivery-ID": delivery_id,
        "X-Bastion-Signature": webhook_signature(
            secret=secret,
            timestamp=timestamp,
            raw_body=raw_body,
            event_type=event_type,
            delivery_id=delivery_id,
        ),
        "X-Bastion-Payload-Version": str(payload_version),
        "X-Bastion-Source": BASTION_WEBHOOK_SOURCE,
    }
    if event_id is not None:
        headers["X-Bastion-Event-ID"] = event_id
    return headers


def verify_signature(
    *,
    secret: str,
    signature_header: str,
    timestamp: int,
    raw_body: str,
    tolerance_seconds: int = DEFAULT_TOLERANCE_SECONDS,
    now: int | None = None,
    delivery_id: str | None = None,
    event_type: str | None = None,
) -> bool:
    """Verify a Bastion webhook signature with timestamp and delivery-id replay guards."""
    if not delivery_id or not event_type:
        return False
    if not signature_header.startswith(SIGNATURE_PREFIX):
        return False
    current = int(time.time()) if now is None else int(now)
    observed = int(timestamp)
    if observed < current - tolerance_seconds or observed > current + tolerance_seconds:
        return False
    expected = webhook_signature(
        secret=secret,
        timestamp=observed,
        raw_body=raw_body,
        event_type=event_type,
        delivery_id=delivery_id,
    )
    return hmac.compare_digest(expected, signature_header)
