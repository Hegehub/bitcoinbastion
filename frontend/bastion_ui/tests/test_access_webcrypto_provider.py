from __future__ import annotations

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from app.services.access.crypto.signatures import Ed25519SignatureSuite  # noqa: E402

from bastion_ui.security.device_provider import (  # noqa: E402
    device_identity_script,
    sign_challenge_script,
)

SIGNING_CONTEXT = "access_challenge"


def test_sp1_nonextractable_key_persists_and_interoperates_with_backend() -> None:
    payload = {
        "protocol": "bastion-access-issuance-v1",
        "operation": "access.issue",
        "checkout_id": "checkout:interop",
        "offer_revision_id": "access-plus:v1",
        "capability": "plus_pass",
        "scopes": ["signals:basic:read"],
        "terms_version": "access-terms-v1",
        "device_key_fingerprint": "bound-by-server-after-identity",
        "nonce": "00" * 32,
        "issued_at": "2026-08-21T00:00:00Z",
        "expires_at": "2026-08-21T00:05:00Z",
    }
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        context = browser.new_context()
        page = context.new_page()
        page.route("https://device.test/", lambda route: route.fulfill(body="<html></html>"))
        page.goto("https://device.test/")
        first = page.evaluate(device_identity_script())
        assert first["ok"] is True
        page.reload()
        second = page.evaluate(device_identity_script())
        assert second["device_public_key"] == first["device_public_key"]
        assert second["device_key_fingerprint"] == first["device_key_fingerprint"]
        payload["device_key_fingerprint"] = first["device_key_fingerprint"]
        import json

        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        signed = page.evaluate(sign_challenge_script(canonical))
        assert signed["ok"] is True
        assert Ed25519SignatureSuite().verify(
            payload, SIGNING_CONTEXT, first["device_public_key"], signed["signature"]
        ).valid
        altered = {**payload, "checkout_id": "checkout:altered"}
        assert not Ed25519SignatureSuite().verify(
            altered, SIGNING_CONTEXT, first["device_public_key"], signed["signature"]
        ).valid
        browser.close()


def test_provider_source_has_no_raw_key_export_or_storage_fallback() -> None:
    source = Path(ROOT / "frontend/bastion_ui/security/device_provider.py").read_text()
    assert "exportKey('pkcs8'" not in source
    assert "exportKey(\"pkcs8\"" not in source
    assert "localStorage" not in source
    assert "sessionStorage" not in source
    assert "get_private_key" not in source
    assert "export_private_key" not in source
