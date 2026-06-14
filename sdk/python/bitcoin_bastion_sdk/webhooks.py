from __future__ import annotations

import hashlib
import hmac
import time


def verify_signature(
    *,
    payload: bytes | str,
    secret: str,
    timestamp: int | str,
    signature: str,
    delivery_id: str | None = None,
    event_type: str | None = None,
    tolerance_seconds: int = 300,
    now: int | None = None,
) -> bool:
    observed = int(now if now is not None else time.time())
    ts = int(timestamp)
    if abs(observed - ts) > tolerance_seconds:
        return False
    if not signature.startswith("v1=") or not delivery_id or not event_type:
        return False
    raw = payload if isinstance(payload, bytes) else payload.encode("utf-8")
    message = f"{ts}.{delivery_id}.{event_type}.".encode("utf-8") + raw
    expected = "v1=" + hmac.new(secret.encode("utf-8"), message, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)
