"""Canonical generated-transport security-provider installation boundary.

Production callers install their provider through ``install_security_provider``.
The environment bootstrap is deliberately limited to the approved ephemeral
browser integration profile; it is inert in every normal runtime profile.
"""

from __future__ import annotations

import base64
import hashlib
import os
import secrets
from collections.abc import Callable
from datetime import UTC, datetime

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from bastion_ui.pop_client import signing_digest
from bastion_ui.transport import foundation
from bastion_ui.transport.foundation import RequestSecurityProvider

_TEST_PROFILE = "ephemeral-device-pop-v1"


class EphemeralBrowserPoPProvider:
    """Request-bound provider used only by the approved live-browser harness."""

    def headers_for(
        self,
        *,
        method: str,
        path: str,
        query_parameters: dict[str, str | int | float | bool | None],
        body: bytes,
    ) -> dict[str, str]:
        timestamp = datetime.now(UTC).isoformat().replace("+00:00", "Z")
        nonce = secrets.token_hex(24)
        digest_hex = signing_digest(
            method, path, query_parameters, body, timestamp, nonce
        ).hex()
        encoded_key = os.environ["P9_TEST_DEVICE_PRIVATE_KEY"]
        private_key = Ed25519PrivateKey.from_private_bytes(
            base64.urlsafe_b64decode(encoded_key + "=" * (-len(encoded_key) % 4))
        )
        message = f"BastionProofOfAccess:v1:access_session\n{digest_hex}".encode()
        signature = base64.urlsafe_b64encode(private_key.sign(message)).decode().rstrip("=")
        token = os.environ["P9_TEST_SESSION_TOKEN"]
        return {
            "Authorization": f"PoP {token}",
            "X-Bastion-Session": token,
            "Bastion-Request-Timestamp": timestamp,
            "Bastion-Request-Nonce": nonce,
            "Bastion-Request-Body-Hash": hashlib.sha256(body).hexdigest(),
            "Bastion-Request-Signature": signature,
        }


def install_security_provider(
    factory: Callable[[], RequestSecurityProvider],
) -> None:
    """Install the sole process-local provider factory used by HttpTransport."""
    foundation.SECURITY_PROVIDER_FACTORY = factory


def install_approved_browser_test_provider() -> bool:
    """Install only under the explicit, ephemeral integration-test profile."""
    if os.environ.get("BASTION_GENERATED_TRANSPORT_SECURITY_PROFILE") != _TEST_PROFILE:
        return False
    if not os.environ.get("P9_TEST_SESSION_TOKEN") or not os.environ.get(
        "P9_TEST_DEVICE_PRIVATE_KEY"
    ):
        raise RuntimeError("ephemeral PoP bootstrap material is incomplete")
    install_security_provider(EphemeralBrowserPoPProvider)
    return True
